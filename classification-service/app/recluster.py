"""
Nightly re-clustering using HDBSCAN.
Discovers clusters automatically from all publication embeddings,
reassigns publications, and generates new labels.
"""

import numpy as np
import hdbscan
from scipy.optimize import linear_sum_assignment
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta
from app.config import settings
from app.db import (
    get_all_embeddings,
    bulk_update_clusters,
    get_connection,
    get_existing_clusters,
    record_cluster_lineage,
    refresh_cluster_exemplars,
    get_cluster_member_publication_ids,
    set_cluster_domain_prior,
    update_cluster_label_and_description,
    update_cluster_tightness,
    insert_or_update_cluster_hierarchy,
    get_cluster_hierarchy,
    insert_or_update_cluster_metrics,
    get_cluster_exemplars,
    get_recent_corrections,
    get_pending_inflow_rates,
    get_pending_pool_count,
    log_clustering_run,
)
from app.clustering import generate_batch_cluster_label
from app.embedding import assert_l2_normalized
from app.llm import generate_cluster_label, generate_taxonomy_label
import logging

logger = logging.getLogger(__name__)


def _compute_cluster_tightness(embeddings: np.ndarray, max_sample: int = 50) -> float:
    """Compute mean pairwise cosine similarity for a cluster."""
    count = embeddings.shape[0]
    if count <= 1:
        return 1.0

    if count > max_sample:
        rng = np.random.default_rng(42)
        sample_indices = rng.choice(count, size=max_sample, replace=False)
        sample = embeddings[sample_indices]
    else:
        sample = embeddings

    similarities = cosine_similarity(sample)
    upper = np.triu_indices_from(similarities, k=1)
    if upper[0].size == 0:
        return 1.0
    return float(similarities[upper].mean())


def _compute_cah_hierarchy(centroids_matrix: np.ndarray, cluster_ids: list[int]) -> dict[int, dict]:
    """
    Compute CAH (Clustering After Hierarchy) on cluster centroids.
    
    Uses scipy hierarchical clustering with cosine distance to produce L1 and L2 labels.
    
    Args:
        centroids_matrix: (N_clusters, embedding_dim) array of cluster centroids.
        cluster_ids: List of cluster IDs corresponding to rows in centroids_matrix.
    
    Returns:
        Dictionary mapping cluster_id to {"l1_label": str, "l2_label": str, "l1_id": int, "l2_id": int}
    """
    if len(cluster_ids) == 0:
        return {}
    
    if len(cluster_ids) == 1:
        # Single cluster: assign to L1_0 and L2_0
        return {
            cluster_ids[0]: {
                "l1_label": "L1_0",
                "l2_label": "L2_0",
                "l1_id": 0,
                "l2_id": 0,
            }
        }
    
    try:
        # Compute pairwise cosine distances (1 - cosine_similarity)
        distances = pdist(centroids_matrix, metric='cosine')
        
        # Perform hierarchical clustering using Ward's method on the distance matrix
        Z = linkage(distances, method='ward')
        
        # Cut dendrogram to get L1 clusters (target: CAH_L1_COUNT)
        l1_count = min(settings.CAH_L1_COUNT, len(cluster_ids))
        l1_labels_raw = fcluster(Z, l1_count, criterion='maxclust')
        
        # Cut dendrogram to get L2 clusters (target: CAH_L2_COUNT)
        l2_count = min(settings.CAH_L2_COUNT, len(cluster_ids))
        l2_labels_raw = fcluster(Z, l2_count, criterion='maxclust')
        
        # Build result mapping
        result = {}
        for idx, cluster_id in enumerate(cluster_ids):
            l1_id = int(l1_labels_raw[idx]) - 1  # fcluster returns 1-indexed
            l2_id = int(l2_labels_raw[idx]) - 1
            result[cluster_id] = {
                "l1_label": f"L1_{l1_id}",
                "l2_label": f"L2_{l2_id}",
                "l1_id": l1_id,
                "l2_id": l2_id,
            }
        
        logger.info(f"CAH computed: {len(result)} clusters -> {l1_count} L1, {l2_count} L2")
        return result
    
    except Exception as e:
        logger.error(f"Error computing CAH hierarchy: {e}")
        # Fallback: assign all to L1_0, L2_0
        return {
            cid: {
                "l1_label": "L1_0",
                "l2_label": "L2_0",
                "l1_id": 0,
                "l2_id": 0,
            }
            for cid in cluster_ids
        }


def _assign_semantic_taxonomy_labels(
    cah_hierarchy: dict[int, dict],
    cluster_info: dict[int, dict]
) -> dict[int, dict]:
    """
    Replace L1/L2 placeholder labels with semantic labels using Gemma.
    """
    if not cah_hierarchy:
        return cah_hierarchy

    l1_groups: dict[int, list[int]] = {}
    l2_groups: dict[int, list[int]] = {}
    for cid, info in cah_hierarchy.items():
        l1_id = info.get("l1_id")
        l2_id = info.get("l2_id")
        if l1_id is not None:
            l1_groups.setdefault(int(l1_id), []).append(cid)
        if l2_id is not None:
            l2_groups.setdefault(int(l2_id), []).append(cid)

    l1_labels: dict[int, str] = {}
    for l1_id, cids in l1_groups.items():
        items = []
        for cid in cids:
            label = cluster_info.get(cid, {}).get("label")
            if label:
                items.append(label)
        label = generate_taxonomy_label(items, level="L1")
        if label:
            l1_labels[l1_id] = label

    l2_labels: dict[int, str] = {}
    for l2_id, cids in l2_groups.items():
        items = []
        parent_label = None
        if cids:
            parent_l1 = cah_hierarchy.get(cids[0], {}).get("l1_id")
            if parent_l1 is not None:
                parent_label = l1_labels.get(int(parent_l1))
        for cid in cids:
            label = cluster_info.get(cid, {}).get("label")
            if label:
                items.append(label)
        label = generate_taxonomy_label(items, level="L2", parent_label=parent_label)
        if label:
            l2_labels[l2_id] = label

    for cid, info in cah_hierarchy.items():
        l1_id = info.get("l1_id")
        l2_id = info.get("l2_id")
        if l1_id is not None and int(l1_id) in l1_labels:
            info["l1_label"] = l1_labels[int(l1_id)]
        if l2_id is not None and int(l2_id) in l2_labels:
            info["l2_label"] = l2_labels[int(l2_id)]

    return cah_hierarchy


def _compute_cluster_metrics(cluster_id: int, member_embeddings: np.ndarray, 
                            member_count: int, old_centroid: list[float] | None = None,
                            new_centroid: list[float] | None = None,
                            label_updated_at: datetime | None = None,
                            correction_counts: dict[int, int] | None = None,
                            pending_inflow_rate: float | None = None) -> dict:
    """
    Compute per-cluster quality and performance metrics.
    
    Args:
        cluster_id: Cluster ID.
        member_embeddings: (N_members, embedding_dim) array of member embeddings.
        member_count: Total number of members in cluster.
        old_centroid: Previous centroid (for drift computation).
        new_centroid: Current centroid (for drift computation).
        label_updated_at: When the cluster label was last updated.
    
    Returns:
        Dictionary with computed metrics.
    """
    metrics = {}
    
    # 1. Intra-cluster mean similarity (tightness)
    if member_embeddings.shape[0] > 1:
        similarities = cosine_similarity(member_embeddings)
        upper = np.triu_indices_from(similarities, k=1)
        if upper[0].size > 0:
            metrics["intra_cluster_mean_similarity"] = float(similarities[upper].mean())
        else:
            metrics["intra_cluster_mean_similarity"] = 1.0
    else:
        metrics["intra_cluster_mean_similarity"] = 1.0
    
    # 2. Member count
    metrics["member_count"] = member_count
    
    # 3. Correction rate in last 30 days
    if correction_counts is not None:
        corrections_for_cluster = int(correction_counts.get(cluster_id, 0))
        if member_count > 0:
            metrics["correction_rate_30d"] = float(corrections_for_cluster) / member_count
        else:
            metrics["correction_rate_30d"] = 0.0
    else:
        metrics["correction_rate_30d"] = None
    
    # 4. Pending inflow rate (new pending per day)
    metrics["pending_inflow_rate"] = pending_inflow_rate
    
    # 5. Centroid drift (cosine distance old vs new)
    if old_centroid is not None and new_centroid is not None:
        try:
            old_vec = np.array(old_centroid).reshape(1, -1)
            new_vec = np.array(new_centroid).reshape(1, -1)
            drift = float(1.0 - cosine_similarity(old_vec, new_vec)[0, 0])
            metrics["centroid_drift"] = drift
        except Exception as e:
            logger.warning(f"Could not compute centroid_drift for cluster {cluster_id}: {e}")
            metrics["centroid_drift"] = None
    else:
        metrics["centroid_drift"] = None
    
    # 6. Last label updated at
    metrics["last_label_updated_at"] = label_updated_at
    
    # 7. Exemplar coverage (exemplars / member_count)
    try:
        exemplars = get_cluster_exemplars(cluster_id)
        if member_count > 0:
            metrics["exemplar_coverage"] = float(len(exemplars)) / member_count
        else:
            metrics["exemplar_coverage"] = 0.0
    except Exception as e:
        logger.warning(f"Could not compute exemplar_coverage for cluster {cluster_id}: {e}")
        metrics["exemplar_coverage"] = None
    
    # 8. Computed at timestamp (will be set by db helper)
    metrics["computed_at"] = datetime.utcnow()
    
    return metrics




def _name_cluster_with_gemma(
    cluster_id: int,
    pub_ids: list[int],
    centroid: list[float],
    l1_label: str | None = None,
    l2_label: str | None = None,
    num_samples: int = 5
) -> dict:
    """
    Use Gemma to generate a cluster name from representative papers.
    
    Samples papers closest to centroid, fetches their text, and calls Gemma
    to generate a canonical name for the cluster.
    
    Args:
        cluster_id: Cluster ID.
        pub_ids: List of publication IDs in cluster.
        l1_label: L1 (top-level) hierarchy label if available.
        l2_label: L2 (sub-category) hierarchy label if available.
        num_samples: Number of representative papers to sample (default 5-10).
    
    Returns:
        Dict with name, description, keywords.
    """
    if not pub_ids:
        return {"name": "Uncategorized", "description": "", "keywords": []}
    if centroid is None:
        return {"name": "Uncategorized", "description": "", "keywords": []}
    
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                # Sample 5-10 papers closest to centroid
                sample_size = min(max(5, num_samples), 10, len(pub_ids))
                cur.execute("""
                    SELECT publication_id, embedding
                    FROM publication_embeddings
                    WHERE publication_id = ANY(%s);
                """, (pub_ids,))
                rows = cur.fetchall()

                sampled_pub_ids: list[int]
                if rows:
                    centroid_vec = np.array(centroid)
                    centroid_norm = float(np.linalg.norm(centroid_vec)) or 1.0
                    scored = []
                    for pub_id, emb in rows:
                        emb_vec = emb.tolist() if hasattr(emb, "tolist") else list(emb)
                        emb_vec = np.array(emb_vec)
                        denom = float(np.linalg.norm(emb_vec) * centroid_norm) or 1.0
                        similarity = float(np.dot(emb_vec, centroid_vec) / denom)
                        scored.append((int(pub_id), similarity))
                    scored.sort(key=lambda x: x[1], reverse=True)
                    sampled_pub_ids = [pid for pid, _ in scored[:sample_size]]
                else:
                    sampled_pub_ids = pub_ids[:sample_size]
                
                # Fetch title and abstract for sampled papers
                cur.execute("""
                    SELECT id, title, abstract_text FROM publications
                    WHERE id = ANY(%s)
                    LIMIT %s;
                """, (sampled_pub_ids, sample_size))
                
                papers = cur.fetchall()
                if not papers:
                    return {"name": "Uncategorized", "description": "", "keywords": []}
                
                texts = []
                for _pid, title, abstract in papers:
                    title = title or ""
                    abstract = abstract or ""
                    texts.append(f"Title: {title}. Abstract: {abstract}")

                # Call Gemma to generate cluster label + description + keywords
                llm_result = generate_cluster_label(texts, l1_label=l1_label, l2_label=l2_label)
                if llm_result.get("name"):
                    logger.info(f"Gemma named cluster {cluster_id}: {llm_result['name']}")
                return llm_result
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error naming cluster {cluster_id} with Gemma: {e}")
        return {"name": "Uncategorized", "description": "", "keywords": []}



def _compute_cluster_domain_prior(cluster_id: int, pub_ids: list[int]) -> tuple[str | None, float]:
    """
    Compute the dominant domain for a cluster using voting.
    
    Checks both publication domain fields and any cluster attributes.
    Uses highest confidence vote.
    
    Args:
        cluster_id: Cluster ID.
        pub_ids: List of publication IDs in cluster.
    
    Returns:
        (dominant_domain, confidence) tuple.
    """
    if not pub_ids:
        return (None, 0.0)
    
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                # Vote from publication domains
                cur.execute("""
                    SELECT domain, COUNT(*) as count
                    FROM publications
                    WHERE id = ANY(%s) AND domain IS NOT NULL
                    GROUP BY domain;
                """, (pub_ids,))
                domain_votes = {row[0]: int(row[1]) for row in cur.fetchall()}

                # Optional vote from cluster attributes (cluster label keywords)
                cur.execute("""
                    SELECT label, keywords
                    FROM clusters
                    WHERE id = %s;
                """, (cluster_id,))
                row = cur.fetchone()
                if row:
                    label, keywords = row[0], row[1]
                    if label:
                        domain_votes[label] = domain_votes.get(label, 0) + 1
                    if keywords:
                        for kw in keywords:
                            domain_votes[kw] = domain_votes.get(kw, 0) + 1

                if not domain_votes:
                    return (None, 0.0)

                dominant = max(domain_votes.items(), key=lambda x: x[1])[0]
                confidence = float(domain_votes[dominant]) / max(len(pub_ids), 1)
                logger.info(f"Cluster {cluster_id} dominant domain: {dominant} ({confidence:.2f})")
                return (dominant, confidence)
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error computing domain prior for cluster {cluster_id}: {e}")
        return (None, 0.0)


def recluster_all() -> dict:
    """
    Re-cluster all publications using HDBSCAN.

    Steps:
        1. Load all embeddings from the database
        2. Run HDBSCAN to discover clusters automatically
        3. Compute centroids for each cluster
        4. Generate labels using TF-IDF on member texts
        5. Bulk update the database

    Returns:
        Summary dict with total_publications, clusters_found, noise_points.
    """
    run_started_at = datetime.utcnow()
    pending_before = get_pending_pool_count()

    # Load all embeddings
    data = get_all_embeddings()
    if not data:
        return {"total_publications": 0, "clusters_found": 0, "noise_points": 0}

    pub_ids = []
    embeddings_list = []
    pending_state = {}
    for pub_id, embedding, pending_since, recluster_attempts in data:
        pub_ids.append(pub_id)
        embeddings_list.append(embedding)
        pending_state[pub_id] = {
            "pending_since": pending_since,
            "recluster_attempts": recluster_attempts,
        }
        assert_l2_normalized(embedding)

    embeddings = np.array(embeddings_list)

    total = len(pub_ids)

    # Not enough data for meaningful clustering
    if total < settings.HDBSCAN_MIN_CLUSTER_SIZE:
        return {"total_publications": total, "clusters_found": 0, "noise_points": total}

    # Run HDBSCAN
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=settings.HDBSCAN_MIN_CLUSTER_SIZE,
        metric="cosine",
        cluster_selection_method="eom",  # Excess of Mass
    )
    labels = clusterer.fit_predict(embeddings)

    # Separate noise (-1) from actual clusters
    unique_labels = set(labels)
    unique_labels.discard(-1)
    noise_count = int(np.sum(labels == -1))

    if len(unique_labels) == 0:
        return {"total_publications": total, "clusters_found": 0, "noise_points": noise_count}

    # Fetch publication texts for label generation
    pub_texts = _fetch_publication_texts(pub_ids)

    # Build new cluster structures
    label_indices = sorted(unique_labels)
    new_centroids = []
    new_labels = []
    new_counts = []
    new_tightness = []
    new_members = []

    for cluster_label_idx in label_indices:
        member_mask = labels == cluster_label_idx
        member_indices = np.where(member_mask)[0]
        member_embeddings = embeddings[member_indices]

        centroid = member_embeddings.mean(axis=0)
        member_texts = [pub_texts.get(pub_ids[i], "") for i in member_indices]
        label = generate_batch_cluster_label(member_texts) if member_texts else "Uncategorized"
        tightness = _compute_cluster_tightness(member_embeddings)

        new_centroids.append(centroid)
        new_labels.append(label)
        new_counts.append(len(member_indices))
        new_tightness.append(tightness)
        new_members.append(member_indices)

    # Stable ID matching
    existing_clusters = get_existing_clusters()
    existing_ids = [c["id"] for c in existing_clusters]
    existing_centroids = [
        (c["centroid"].tolist() if hasattr(c["centroid"], "tolist") else list(c["centroid"]))
        for c in existing_clusters
    ]
    existing_labels = {c["id"]: c["label"] for c in existing_clusters}

    stable_id_map: dict[int, int] = {}
    stable_label_map: dict[int, str] = {}
    lineage_mappings: list[tuple[int | None, int, float]] = []
    next_cluster_id = (max(existing_ids) + 1) if existing_ids else 1

    if existing_centroids and new_centroids:
        similarities = cosine_similarity(np.array(new_centroids), np.array(existing_centroids))
        cost_matrix = 1 - similarities
        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        for row_idx, col_idx in zip(row_ind, col_ind):
            similarity = float(similarities[row_idx, col_idx])
            if similarity >= settings.STABLE_ID_SIMILARITY_THRESHOLD:
                old_id = existing_ids[col_idx]
                stable_id_map[row_idx] = old_id
                stable_label_map[old_id] = existing_labels.get(old_id) or new_labels[row_idx]
                lineage_mappings.append((old_id, old_id, similarity))

    for row_idx in range(len(new_centroids)):
        if row_idx in stable_id_map:
            continue
        assigned_id = next_cluster_id
        next_cluster_id += 1
        stable_id_map[row_idx] = assigned_id
        stable_label_map[assigned_id] = new_labels[row_idx]

    # Build cluster info
    cluster_assignments = {}  # {pub_id: {"cluster_id": int, "suggested_cluster_id": int|None, "pending_since": dt, "recluster_attempts": int}}
    cluster_info = {}  # {cluster_id: {"label": str, "centroid": list, "count": int, "tightness": float}}

    centroid_matrix = []
    centroid_ids = []

    for row_idx, cluster_label_idx in enumerate(label_indices):
        assigned_cluster_id = stable_id_map[row_idx]
        label = stable_label_map[assigned_cluster_id]
        centroid = new_centroids[row_idx]
        count = new_counts[row_idx]
        tightness = new_tightness[row_idx]

        cluster_info[assigned_cluster_id] = {
            "label": label,
            "centroid": centroid.tolist(),
            "count": count,
            "tightness": tightness,
        }

        centroid_matrix.append(centroid)
        centroid_ids.append(assigned_cluster_id)

        for idx in new_members[row_idx]:
            pub_id = pub_ids[idx]
            cluster_assignments[pub_id] = {
                "cluster_id": assigned_cluster_id,
                "suggested_cluster_id": None,
                "pending_since": None,
                "recluster_attempts": 0,
            }

    # Handle noise points (-1): calculate soft assignment using memory centroids
    if noise_count > 0 and len(centroid_matrix) > 0:
        centroid_matrix = np.array(centroid_matrix)
        noise_indices = np.where(labels == -1)[0]
        now = datetime.utcnow()

        for idx in noise_indices:
            embedding = embeddings[idx].reshape(1, -1)
            similarities = cosine_similarity(embedding, centroid_matrix)[0]

            best_idx = int(np.argmax(similarities))
            best_sim = float(similarities[best_idx])

            suggested_cid = None
            if best_sim >= settings.SOFT_SIMILARITY_THRESHOLD:
                suggested_cid = centroid_ids[best_idx]

            pub_id = pub_ids[idx]
            previous_pending = pending_state.get(pub_id, {})
            pending_since = previous_pending.get("pending_since")
            attempts = int(previous_pending.get("recluster_attempts") or 0)

            if pending_since:
                # Already in the pending pool — increment attempt counter
                attempts += 1
                if attempts >= settings.PENDING_RECLUSTER_ATTEMPTS:
                    # Exhausted retries — promote to permanent unclustered
                    pending_since = None
                    attempts = 0
            elif suggested_cid is not None:
                # First-time noise but close enough to a centroid → enter pending pool
                # so it can be reconsidered in the next HDBSCAN run.
                pending_since = now
                attempts = 1
            # else: sim < SOFT_SIMILARITY_THRESHOLD → genuine outlier, stays unclustered

            cluster_assignments[pub_id] = {
                "cluster_id": -1,
                "suggested_cluster_id": suggested_cid,
                "pending_since": pending_since,
                "recluster_attempts": attempts,
            }
    elif noise_count > 0:
        # Fallback when no valid clusters exist yet (cold-start scenario)
        noise_indices = np.where(labels == -1)[0]
        now = datetime.utcnow()
        for idx in noise_indices:
            pub_id = pub_ids[idx]
            previous_pending = pending_state.get(pub_id, {})
            pending_since = previous_pending.get("pending_since")
            attempts = int(previous_pending.get("recluster_attempts") or 0)

            if pending_since:
                attempts += 1
                if attempts >= settings.PENDING_RECLUSTER_ATTEMPTS:
                    pending_since = None
                    attempts = 0
            else:
                # No clusters exist yet — enter pending pool so they are included
                # in the next run once enough papers accumulate.
                pending_since = now
                attempts = 1

            cluster_assignments[pub_id] = {
                "cluster_id": -1,
                "suggested_cluster_id": None,
                "pending_since": pending_since,
                "recluster_attempts": attempts,
            }

    # Bulk update database
    bulk_update_clusters(cluster_assignments, cluster_info)
    record_cluster_lineage(lineage_mappings)
    
    # PHASE 3: Refresh exemplars, compute domain priors, and name clusters with Gemma
    # PHASE 4: Compute CAH hierarchy, compute metrics, and use L1/L2 context in naming
    if len(unique_labels) > 0:
        # Build mapping of cluster_id to publication_ids for exemplar refresh
        cluster_members = {}
        for pub_id, assignment in cluster_assignments.items():
            cid = assignment.get("cluster_id")
            if cid != -1:
                if cid not in cluster_members:
                    cluster_members[cid] = []
                cluster_members[cid].append(pub_id)
        
        # Refresh exemplars
        if cluster_members:
            logger.info(f"Refreshing exemplars for {len(cluster_members)} clusters...")
            refresh_cluster_exemplars(cluster_members)
        
        # PHASE 4: Compute CAH hierarchy on centroids
        if len(centroid_matrix) > 0:
            centroid_matrix_np = np.array(centroid_matrix)
            cah_hierarchy = _compute_cah_hierarchy(centroid_matrix_np, centroid_ids)
            cah_hierarchy = _assign_semantic_taxonomy_labels(cah_hierarchy, cluster_info)
            logger.info(f"CAH hierarchy computed for {len(cah_hierarchy)} clusters")
        else:
            cah_hierarchy = {}
            logger.warning("No centroids available for CAH computation")
        
        # PHASE 4: Precompute correction counts and pending inflow rates
        correction_counts: dict[int, int] = {}
        try:
            recent_corrections = get_recent_corrections(days=settings.CORRECTION_WINDOW_DAYS)
            for correction in recent_corrections:
                assigned_cluster = int(correction["assigned_cluster_id"])
                correction_counts[assigned_cluster] = correction_counts.get(assigned_cluster, 0) + 1
        except Exception as e:
            logger.warning(f"Could not load recent corrections: {e}")
        
        pending_inflow_rates = {}
        try:
            pending_inflow_rates = get_pending_inflow_rates(days=1)
        except Exception as e:
            logger.warning(f"Could not compute pending inflow rates: {e}")
        
        # PHASE 4: Threshold calibration based on correction rate
        for cid, info in cluster_info.items():
            current_tightness = info.get("tightness")
            if current_tightness is None:
                continue
            correction_rate = 0.0
            if correction_counts and cid in correction_counts and info.get("count"):
                correction_rate = float(correction_counts[cid]) / float(info.get("count") or 1)
            new_tightness = current_tightness
            if correction_rate > settings.CORRECTION_RATE_HIGH:
                new_tightness = min(1.0, current_tightness + settings.THRESHOLD_TIGHTEN_DELTA)
            elif correction_rate < settings.CORRECTION_RATE_LOW:
                new_tightness = max(0.0, current_tightness - settings.THRESHOLD_RELAX_DELTA)
            if new_tightness != current_tightness:
                update_cluster_tightness(cid, new_tightness)
                cluster_info[cid]["tightness"] = new_tightness
                logger.info(
                    f"Calibrated cluster {cid} tightness {current_tightness:.3f} -> {new_tightness:.3f} "
                    f"(correction_rate={correction_rate:.3f})"
                )
        
        # Compute domain priors, CAH hierarchy, and metrics for each cluster
        for cid in cluster_members.keys():
            member_ids = cluster_members[cid]
            
            # Compute domain prior
            dominant_domain, confidence = _compute_cluster_domain_prior(cid, member_ids)
            if dominant_domain:
                set_cluster_domain_prior(cid, dominant_domain, confidence)
            
            # PHASE 4: Store CAH hierarchy
            hierarchy_info = cah_hierarchy.get(cid, {})
            if hierarchy_info:
                insert_or_update_cluster_hierarchy(
                    cid, 
                    hierarchy_info.get("l1_label"), 
                    hierarchy_info.get("l2_label"),
                    hierarchy_info.get("l1_id"), 
                    hierarchy_info.get("l2_id")
                )
                logger.debug(f"Stored CAH hierarchy for cluster {cid}: {hierarchy_info}")
            
            # PHASE 4: Compute and store metrics
            try:
                # Get member embeddings for metric computation
                conn = get_connection()
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT embedding FROM publication_embeddings
                            WHERE publication_id = ANY(%s);
                        """, (member_ids,))
                        member_embeddings = np.array([
                            row[0].tolist() if hasattr(row[0], "tolist") else list(row[0])
                            for row in cur.fetchall()
                        ])
                finally:
                    conn.close()
                
                # Get old centroid if exists (for drift computation)
                old_centroid = None
                try:
                    old_cluster = next((c for c in existing_clusters if c["id"] == cid), None)
                    if old_cluster and old_cluster["centroid"]:
                        old_centroid = (old_cluster["centroid"].tolist() if hasattr(old_cluster["centroid"], "tolist") 
                                       else list(old_cluster["centroid"]))
                except Exception as e:
                    logger.warning(f"Could not retrieve old centroid for cluster {cid}: {e}")
                
                # Get new centroid
                new_centroid = cluster_info[cid]["centroid"] if cid in cluster_info else None
                
                # Compute metrics
                metrics = _compute_cluster_metrics(
                    cid,
                    member_embeddings,
                    len(member_ids),
                    old_centroid,
                    new_centroid,
                    label_updated_at=None,  # Will be updated when label is set
                    correction_counts=correction_counts,
                    pending_inflow_rate=pending_inflow_rates.get(cid)
                )
                
                # Store metrics
                insert_or_update_cluster_metrics(
                    cid,
                    intra_cluster_mean_similarity=metrics.get("intra_cluster_mean_similarity"),
                    member_count=metrics.get("member_count"),
                    correction_rate_30d=metrics.get("correction_rate_30d"),
                    pending_inflow_rate=metrics.get("pending_inflow_rate"),
                    centroid_drift=metrics.get("centroid_drift"),
                    last_label_updated_at=metrics.get("last_label_updated_at"),
                    exemplar_coverage=metrics.get("exemplar_coverage")
                )
                logger.debug(f"Stored metrics for cluster {cid}")
                
            except Exception as e:
                logger.error(f"Error computing metrics for cluster {cid}: {e}")
            
            # PHASE 4 + Name cluster with Gemma (using L1/L2 context if available)
            try:
                l1_label = hierarchy_info.get("l1_label") if hierarchy_info else None
                l2_label = hierarchy_info.get("l2_label") if hierarchy_info else None
                
                centroid = cluster_info.get(cid, {}).get("centroid")
                label_result = _name_cluster_with_gemma(
                    cid,
                    member_ids,
                    centroid=centroid,
                    l1_label=l1_label,
                    l2_label=l2_label,
                    num_samples=min(10, len(member_ids))
                )
                label_name = label_result.get("name") if label_result else None
                if label_name and label_name != "Uncategorized":
                    update_cluster_label_and_description(
                        cid,
                        label_name,
                        description=label_result.get("description"),
                        keywords=label_result.get("keywords")
                    )
                    # Update metrics with label update timestamp
                    insert_or_update_cluster_metrics(
                        cid,
                        last_label_updated_at=datetime.utcnow()
                    )
                    logger.info(f"Updated cluster {cid} label with Gemma: {label_name} (L1: {l1_label}, L2: {l2_label})")
            except Exception as e:
                logger.warning(f"Gemma naming failed for cluster {cid}, keeping TF-IDF label: {e}")

    # G3: write structured run audit log
    run_finished_at = datetime.utcnow()
    clusters_after = len(unique_labels)
    id_matches_reused_count = len(lineage_mappings)
    new_clusters_count = clusters_after - id_matches_reused_count
    pending_after = get_pending_pool_count()
    try:
        log_clustering_run(
            started_at=run_started_at,
            finished_at=run_finished_at,
            total_publications=total,
            clusters_before=len(existing_ids),
            clusters_after=clusters_after,
            new_clusters=max(0, new_clusters_count),
            id_matches_reused=id_matches_reused_count,
            noise_points=noise_count,
            pending_before=pending_before,
            pending_after=pending_after,
        )
    except Exception as _log_err:
        logger.warning("Could not write clustering run log: %s", _log_err)

    return {
        "total_publications": total,
        "clusters_found": clusters_after,
        "noise_points": noise_count,
        "id_matches_reused": id_matches_reused_count,
        "new_clusters": max(0, new_clusters_count),
        "duration_seconds": (run_finished_at - run_started_at).total_seconds(),
        "pending_before": pending_before,
        "pending_after": pending_after,
    }



def _fetch_publication_texts(pub_ids: list[int]) -> dict[int, str]:
    """
    Fetch title + abstract for publications to generate cluster labels.

    Args:
        pub_ids: List of publication IDs.

    Returns:
        Dict mapping publication_id to combined text.
    """
    if not pub_ids:
        return {}

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, COALESCE(title, '') || '. ' || COALESCE(abstract_text, '')
                FROM publications
                WHERE id = ANY(%s);
            """, (pub_ids,))
            return {row[0]: row[1] for row in cur.fetchall()}
    finally:
        conn.close()
