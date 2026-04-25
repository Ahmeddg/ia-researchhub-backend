"""
Nightly re-clustering using HDBSCAN.
Discovers clusters automatically from all publication embeddings,
reassigns publications, and generates new labels.
"""

import numpy as np
import hdbscan
from sklearn.metrics.pairwise import cosine_similarity
from app.config import settings
from app.db import get_all_embeddings, bulk_update_clusters, get_connection
from app.clustering import generate_batch_cluster_label


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
    # Load all embeddings
    data = get_all_embeddings()
    if not data:
        return {"total_publications": 0, "clusters_found": 0, "noise_points": 0}

    pub_ids = [d[0] for d in data]
    embeddings = np.array([d[1] for d in data])

    total = len(pub_ids)

    # Not enough data for meaningful clustering
    if total < settings.HDBSCAN_MIN_CLUSTER_SIZE:
        return {"total_publications": total, "clusters_found": 0, "noise_points": total}

    # Run HDBSCAN
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=settings.HDBSCAN_MIN_CLUSTER_SIZE,
        metric="euclidean",
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

    # Build cluster info
    cluster_assignments = {}  # {pub_id: {"cluster_id": int, "suggested_cluster_id": int|None}}
    cluster_info = {}  # {cluster_id: {"label": str, "centroid": list, "count": int}}
    
    # Store centroids in memory for fast outlier matching
    centroid_matrix = []
    centroid_ids = []

    for cluster_label_idx in unique_labels:
        new_cluster_id = int(cluster_label_idx) + 1  # 1-indexed

        # Get member indices
        member_mask = labels == cluster_label_idx
        member_indices = np.where(member_mask)[0]

        # Compute centroid
        member_embeddings = embeddings[member_indices]
        centroid = member_embeddings.mean(axis=0)

        # Gather texts for label generation
        member_texts = [pub_texts.get(pub_ids[i], "") for i in member_indices]
        label = generate_batch_cluster_label(member_texts) if member_texts else "Uncategorized"

        cluster_info[new_cluster_id] = {
            "label": label,
            "centroid": centroid.tolist(),
            "count": len(member_indices),
        }

        # Collect for fast similarity lookup
        centroid_matrix.append(centroid)
        centroid_ids.append(new_cluster_id)

        # Assign publications
        for idx in member_indices:
            cluster_assignments[pub_ids[idx]] = {"cluster_id": new_cluster_id, "suggested_cluster_id": None}

    # Handle noise points (-1): calculate soft assignment using memory centroids
    if noise_count > 0 and len(centroid_matrix) > 0:
        centroid_matrix = np.array(centroid_matrix)
        noise_indices = np.where(labels == -1)[0]
        
        for idx in noise_indices:
            embedding = embeddings[idx].reshape(1, -1)
            # Compute cosine similarity
            similarities = cosine_similarity(embedding, centroid_matrix)[0]
            
            best_idx = np.argmax(similarities)
            best_sim = similarities[best_idx]
            
            suggested_cid = None
            if best_sim >= settings.SOFT_SIMILARITY_THRESHOLD:
                suggested_cid = centroid_ids[best_idx]
                
            cluster_assignments[pub_ids[idx]] = {
                "cluster_id": -1, 
                "suggested_cluster_id": suggested_cid
            }
    elif noise_count > 0:
        # Fallback if no valid clusters exist
        noise_indices = np.where(labels == -1)[0]
        for idx in noise_indices:
            cluster_assignments[pub_ids[idx]] = {"cluster_id": -1, "suggested_cluster_id": None}

    # Bulk update database
    bulk_update_clusters(cluster_assignments, cluster_info)

    return {
        "total_publications": total,
        "clusters_found": len(unique_labels),
        "noise_points": noise_count,
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
