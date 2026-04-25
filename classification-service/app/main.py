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
    try_advisory_lock,
    unlock_advisory_lock
)
from app.clustering import assign_cluster
from app.recluster import recluster_all
import logging
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
    PersonalizedRecommendationRequest
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
        if total_count > 0 and total_count % 10 == 0:
            logger.info(f"Total publications reached {total_count}. Attempting to trigger batch clustering...")
            if try_advisory_lock():
                logger.info("Advisory lock acquired. Running batch clustering.")
                try:
                    recluster_all()
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
        cluster_id, cluster_label, confidence, llm_result, suggested_id, suggested_label = assign_cluster(
            publication_id=request.publication_id,
            title=request.title,
            abstract_text=request.abstract_text,
            domain=request.domain,
            pdf_url=request.pdf_url,
        )

        # Queue the job check asynchronously
        background_tasks.add_task(check_and_trigger_reclustering)

        return ClassifyResponse(
            publication_id=request.publication_id,
            cluster_id=cluster_id,
            cluster_label=cluster_label,
            confidence=round(confidence, 4),
            categories=llm_result.get("predicted_categories", []),
            keywords=llm_result.get("keywords", []),
            suggested_cluster_id=suggested_id,
            suggested_cluster_label=suggested_label
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


@app.get("/clusters/{cluster_id}", response_model=ClusterDetail)
async def get_cluster(cluster_id: int):
    """Get detailed information about a specific cluster."""
    detail = get_cluster_detail(cluster_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
    return ClusterDetail(**detail)


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


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        model_loaded=is_model_loaded(),
    )


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
