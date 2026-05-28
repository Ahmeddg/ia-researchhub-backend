"""
FastAPI application for the classification microservice.
Provides endpoints to classify publications, manage clusters,
and trigger re-clustering.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from app.config import settings
from app.embedding import load_model, is_model_loaded
from app.db import (
    init_db,
    get_all_clusters,
    get_cluster_detail,
    get_total_publication_count,
    get_pending_pool_count,
    get_clustering_state,
    update_clustering_state,
    try_advisory_lock,
    unlock_advisory_lock,
    insert_classification_correction,
    get_cluster_metrics,
    get_all_cluster_metrics,
    refresh_cluster_exemplars,
    get_cluster_member_publication_ids,
    get_clustering_run_log,
    get_recent_corrections,
    get_taxonomy_tree,
    sync_cluster_metrics_counts,
)
from app.clustering import assign_cluster
from app.recluster import recluster_all
import logging
from datetime import datetime
from app.recommend import (
    recommend_similar_publications,
    recommend_with_cluster_filter,
    detect_close_pairs,
    recommend_personalized
)
from app.schemas import (
    ClassifyRequest,
    ClassifyResponse,
    ClusterInfo,
    ClusterDetail,
    ReclusterResponse,
    HealthResponse,
    RecommendationResponse,
    ClosePair,
    PersonalizedRecommendationRequest,
    SubmitCorrectionRequest,
    CorrectionResponse,
    ClusterMetricsResponse,
    ClusteringRunLogEntry,
    SystemConfig,
    SystemConfigUpdate,
    CorrectionEntry,
    TaxonomyTreeResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: initialize DB and load the embedding model
    print("=" * 60)
    print("Classification Service starting up...")
    print(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    print(f"Model: {settings.MODEL_NAME}")
    print(f"Similarity threshold: {settings.SIMILARITY_THRESHOLD}")
    print("=" * 60)

    init_db()
    load_model()

    print("Classification Service is ready!")
    yield
    # Shutdown
    print("Classification Service shutting down...")


app = FastAPI(
    title="Publication Classification Service",
    description="AI-powered automatic classification of scientific publications "
                "using sentence embeddings and clustering.",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Endpoints ────────────────────────────────────────────────────────────────


logger = logging.getLogger(__name__)

def check_and_trigger_reclustering():
    """ Runs as a BackgroundTask after classification to trigger batch HDBSCAN at interval thresholds. """
    try:
        total_count = get_total_publication_count()
        pending_count = get_pending_pool_count()
        last_run_at, last_publication_count = get_clustering_state()

        new_papers = max(total_count - last_publication_count, 0)
        now = datetime.utcnow()
        hours_since_last = (
            (now - last_run_at).total_seconds() / 3600
            if last_run_at
            else float("inf")
        )

        should_run = (
            new_papers >= settings.RECLUSTER_MIN_NEW_PAPERS
            or pending_count > settings.RECLUSTER_PENDING_THRESHOLD
            or hours_since_last >= settings.RECLUSTER_MAX_INTERVAL_HOURS
        )

        if should_run:
            logger.info(
                "Triggering batch clustering: new_papers=%s pending=%s hours_since_last=%.2f",
                new_papers,
                pending_count,
                hours_since_last,
            )
            if try_advisory_lock():
                logger.info("Advisory lock acquired. Running batch clustering.")
                try:
                    recluster_all()
                    update_clustering_state(now, total_count)
                    logger.info("Batch clustering completed successfully.")
                finally:
                    unlock_advisory_lock()
            else:
                logger.info("Another process is currently running batch clustering. Skipping.")
    except Exception as e:
        logger.error(f"Error checking or triggering reclustering: {e}")

@app.post("/classify", response_model=ClassifyResponse)
async def classify_publication(request: ClassifyRequest, background_tasks: BackgroundTasks):
    """
    Classify a publication by assigning it to a cluster.

    Takes the publication's title, abstract, and optionally a PDF URL.
    Combines all text sources (title + abstract + first 2-3 PDF pages)
    to generate a rich embedding for better classification accuracy.
    """
    try:
        cluster_id, cluster_label, confidence, llm_result, suggested_id, suggested_label, explainability_score = assign_cluster(
            publication_id=request.publication_id,
            title=request.title,
            abstract_text=request.abstract_text,
            domain=request.domain,
            pdf_url=request.pdf_url,
        )

        # Queue background tasks: trigger check + sync metrics counts
        background_tasks.add_task(check_and_trigger_reclustering)
        background_tasks.add_task(sync_cluster_metrics_counts)

        return ClassifyResponse(
            publication_id=request.publication_id,
            cluster_id=cluster_id,
            cluster_label=cluster_label,
            confidence=round(confidence, 4),
            categories=llm_result.get("predicted_categories", []),
            keywords=llm_result.get("keywords", []),
            suggested_cluster_id=suggested_id,
            suggested_cluster_label=suggested_label,
            explainability_score=round(explainability_score, 4) if explainability_score is not None else None
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@app.post("/recluster", response_model=ReclusterResponse)
async def trigger_recluster():
    """
    Trigger a full re-clustering of all publications using HDBSCAN.

    This is computationally expensive — typically run as a nightly batch job.
    All existing cluster assignments are recalculated.
    """
    try:
        result = recluster_all()
        return ReclusterResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Re-clustering failed: {str(e)}")


@app.get("/clusters", response_model=list[ClusterInfo])
async def list_clusters():
    """List all clusters with their labels and member counts."""
    clusters = get_all_clusters()
    return [ClusterInfo(**c) for c in clusters]


@app.get("/clusters/metrics", response_model=list[ClusterMetricsResponse])
async def get_clusters_metrics(order_by: str = "computed_at", descending: bool = True):
    """
    Get per-cluster metrics for all clusters.
    
    Returns quality and performance indicators for each cluster including:
    - Intra-cluster mean similarity (cohesion)
    - Member count
    - Correction rate (30-day window)
    - Pending inflow rate
    - Centroid drift
    - Label update timestamp
    - Exemplar coverage
    
    Args:
        order_by: Column to order by (e.g., 'correction_rate_30d', 'centroid_drift', 'computed_at')
        descending: If True, order DESC, else ASC
    
    Returns:
        List of ClusterMetricsResponse objects
    """
    try:
        metrics = get_all_cluster_metrics(order_by=order_by, descending=descending)
        return [ClusterMetricsResponse(**m) for m in metrics]
    except Exception as e:
        logger.error(f"Error fetching cluster metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch cluster metrics: {str(e)}")


@app.get("/clusters/{cluster_id}", response_model=ClusterDetail)
async def get_cluster(cluster_id: int):
    """Get detailed information about a specific cluster."""
    detail = get_cluster_detail(cluster_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
    return ClusterDetail(**detail)


@app.get("/corrections", response_model=list[CorrectionEntry])
async def get_corrections_list(page: int = 0, page_size: int = 20):
    """Get recent classification corrections."""
    try:
        corrections = get_recent_corrections(page=page, page_size=page_size)
        return [CorrectionEntry(**c) for c in corrections]
    except Exception as e:
        logger.error(f"Error fetching corrections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/corrections", response_model=CorrectionResponse)
async def submit_correction(request: SubmitCorrectionRequest):
    """
    Submit a classification correction for a publication.
    
    Records the correction feedback and seeds exemplars for the correct cluster.
    
    Args:
        publication_id: ID of the publication being corrected
        assigned_cluster_id: Cluster ID assigned by the algorithm
        correct_cluster_id: Correct cluster ID per human feedback
        corrected_by: Username or identifier of the corrector
        confidence: Confidence score for the correction (0-1)
    
    Returns:
        Confirmation with exemplars_seeded flag
    """
    try:
        # Store the correction in the database
        insert_classification_correction(
            publication_id=request.publication_id,
            assigned_cluster_id=request.assigned_cluster_id,
            correct_cluster_id=request.correct_cluster_id,
            corrected_by=request.corrected_by,
            confidence=request.confidence
        )
        
        # Update the publication's cluster assignment
        correct_cluster = get_cluster_detail(request.correct_cluster_id)
        if correct_cluster:
            from app.db import get_connection
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE publications 
                        SET cluster_id = %s, cluster_label = %s, 
                            suggested_cluster_id = NULL, suggested_cluster_label = NULL 
                        WHERE id = %s
                    """, (request.correct_cluster_id, correct_cluster.get("label"), request.publication_id))
                    conn.commit()
            finally:
                conn.close()
        
        # Seed exemplars for the correct cluster
        exemplars_seeded = False
        try:
            pub_ids = get_cluster_member_publication_ids(request.correct_cluster_id)
            if request.publication_id not in pub_ids:
                pub_ids.append(request.publication_id)
                
            if pub_ids:
                refresh_cluster_exemplars({request.correct_cluster_id: pub_ids})
                exemplars_seeded = True
        except Exception as e:
            logger.error(f"Error seeding exemplars for cluster {request.correct_cluster_id}: {e}")
            # Continue anyway - the correction was recorded even if exemplar seeding failed
        
        return CorrectionResponse(
            publication_id=request.publication_id,
            assigned_cluster_id=request.assigned_cluster_id,
            correct_cluster_id=request.correct_cluster_id,
            corrected_by=request.corrected_by,
            confidence=request.confidence,
            exemplars_seeded=exemplars_seeded
        )
    except Exception as e:
        logger.error(f"Error submitting correction: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit correction: {str(e)}")





@app.get("/recommendations/{publication_id}", response_model=list[RecommendationResponse])
async def get_recommendations(publication_id: int, mode: str = "global", limit: int = 5):
    """
    Get similar publications for a given publication.
    mode can be 'global' (all publications) or 'cluster' (only within the same cluster).
    """
    try:
        if mode == "cluster":
            results = recommend_with_cluster_filter(publication_id, top_k=limit)
        else:
            results = recommend_similar_publications(publication_id, top_k=limit)
            
        return [RecommendationResponse(**r) for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recommend/personalized", response_model=list[RecommendationResponse])
async def get_personalized_recommendations(request: PersonalizedRecommendationRequest):
    """
    Get personalized recommendations based on the user's vote history.
    """
    try:
        results = recommend_personalized(request.upvotedIds, request.downvotedIds, top_k=request.limit)
        return [RecommendationResponse(**r) for r in results]
    except Exception as e:
        logger.error(f"Personalized recommendations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        

@app.get("/close-pairs", response_model=list[ClosePair])
async def get_close_pairs(threshold: float = 0.90):
    """
    Find pairs of publications that are very similar to each other.
    """
    try:
        results = detect_close_pairs(threshold)
        return [ClosePair(**r) for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/recluster/history", response_model=list[ClusteringRunLogEntry])
async def get_recluster_history(limit: int = 20):
    """
    Return the structured audit log for recent HDBSCAN recluster runs.

    Each entry contains: run duration, total publications processed,
    clusters before/after, new clusters vs stable ID matches,
    noise points, and pending pool size change.

    Args:
        limit: Maximum number of entries to return (default 20, newest first).
    """
    try:
        entries = get_clustering_run_log(limit=limit)
        return [ClusteringRunLogEntry(**e) for e in entries]
    except Exception as e:
        logger.error(f"Error fetching recluster history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch recluster history: {str(e)}")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        embedding_model=settings.MODEL_NAME,
        model_loaded=is_model_loaded()
    )


@app.get("/config", response_model=SystemConfig)
async def get_system_config():
    """Get the current dynamic system configuration."""
    try:
        return SystemConfig(**settings.get_all_dynamic_configs())
    except Exception as e:
        logger.error(f"Error fetching config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch config: {str(e)}")


@app.put("/config", response_model=dict)
async def update_system_config(update: SystemConfigUpdate):
    """
    Update a dynamic system configuration key.
    Writes to the database so it persists across restarts.
    """
    if update.key not in settings._defaults:
        raise HTTPException(status_code=400, detail=f"Invalid configuration key: {update.key}")
    
    try:
        # Validate type
        type_func = settings._defaults[update.key][1]
        try:
            type_func(update.value)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid type for {update.key}. Expected {type_func.__name__}.")
        
        from app.db import upsert_system_config
        upsert_system_config(update.key, update.value)
        
        # Force cache refresh in this worker
        settings._cache[update.key] = update.value
        
        return {"status": "success", "message": f"Updated {update.key}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


@app.get("/taxonomy", response_model=TaxonomyTreeResponse)
async def get_taxonomy():
    """
    Get the L1/L2 hierarchical taxonomy tree of clusters.
    """
    try:
        tree = get_taxonomy_tree()
        return TaxonomyTreeResponse(**tree)
    except Exception as e:
        logger.error(f"Error fetching taxonomy tree: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch taxonomy tree: {str(e)}")


@app.post("/sync-metrics", response_model=dict)
async def sync_metrics():
    """
    Sync cluster_metrics.member_count from the authoritative clusters table.

    Call this after any incremental classification to ensure the metrics
    table reflects the current cluster sizes without waiting for a full recluster.
    """
    try:
        result = sync_cluster_metrics_counts()
        return {"status": "ok", **result}
    except Exception as e:
        logger.error(f"Error syncing cluster metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
