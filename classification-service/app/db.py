"""
Database operations for pgvector-powered classification.
Manages the publication_embeddings and clusters tables.
"""

from datetime import datetime
import psycopg2
import psycopg2.extras
from pgvector.psycopg2 import register_vector
from app.config import settings
from app.embedding import assert_l2_normalized


def get_connection():
    """Get a new database connection."""
    conn = psycopg2.connect(settings.DATABASE_URL)
    return conn

def register_vector_safely(conn):
    """Register vector type if the extension exists."""
    try:
        register_vector(conn)
    except:
        # Extension might not be installed yet
        pass


def init_db():
    """
    Initialize the database: enable pgvector extension and create
    the publication_embeddings and clusters tables if they don't exist.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # First, check/create the extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()
            
            # Now we can safely register vector types for this connection
            register_vector_safely(conn)
            
            # Table to store publication embeddings
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS publication_embeddings (
                    publication_id BIGINT PRIMARY KEY,
                    embedding vector({settings.EMBEDDING_DIM}) NOT NULL
                );
            """)

            # Table to store cluster centroids and metadata
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS clusters (
                    id SERIAL PRIMARY KEY,
                    label VARCHAR(200),
                    description TEXT,
                    keywords TEXT[],
                    centroid vector({settings.EMBEDDING_DIM}),
                    cluster_tightness DOUBLE PRECISION,
                    member_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)

            cur.execute("""
                ALTER TABLE publication_embeddings
                ADD COLUMN IF NOT EXISTS pending_since TIMESTAMP;
            """)
            cur.execute("""
                ALTER TABLE publication_embeddings
                ADD COLUMN IF NOT EXISTS recluster_attempts INTEGER DEFAULT 0;
            """)
            cur.execute("""
                ALTER TABLE clusters
                ADD COLUMN IF NOT EXISTS cluster_tightness DOUBLE PRECISION;
            """)
            cur.execute("""
                ALTER TABLE clusters
                ADD COLUMN IF NOT EXISTS description TEXT;
            """)
            cur.execute("""
                ALTER TABLE clusters
                ADD COLUMN IF NOT EXISTS keywords TEXT[];
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS cluster_lineage (
                    id SERIAL PRIMARY KEY,
                    old_cluster_id INTEGER,
                    new_cluster_id INTEGER NOT NULL,
                    similarity_score DOUBLE PRECISION,
                    matched_at TIMESTAMP DEFAULT NOW()
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS clustering_state (
                    id INTEGER PRIMARY KEY,
                    last_run_at TIMESTAMP,
                    last_publication_count INTEGER DEFAULT 0
                );
            """)
            cur.execute("""
                INSERT INTO clustering_state (id, last_publication_count)
                VALUES (1, 0)
                ON CONFLICT (id) DO NOTHING;
            """)

            # Phase 4: Pending inflow events for accurate rate tracking
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pending_inflow_events (
                    id SERIAL PRIMARY KEY,
                    publication_id BIGINT NOT NULL,
                    suggested_cluster_id INTEGER,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)

            # Phase 3: Exemplars table (K papers closest to centroid per cluster)
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS cluster_exemplars (
                    id SERIAL PRIMARY KEY,
                    cluster_id INTEGER NOT NULL REFERENCES clusters(id),
                    publication_id BIGINT NOT NULL,
                    distance_to_centroid DOUBLE PRECISION,
                    exemplar_rank INTEGER,
                    updated_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(cluster_id, publication_id)
                );
            """)

            # Phase 3: Domain prior table (dominant domain per cluster)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cluster_domain_prior (
                    cluster_id INTEGER PRIMARY KEY REFERENCES clusters(id),
                    dominant_domain VARCHAR(100),
                    confidence DOUBLE PRECISION,
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)

            # Phase 4: Cluster hierarchy (L1/L2 labels and IDs)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cluster_hierarchy (
                    id SERIAL PRIMARY KEY,
                    cluster_id INTEGER NOT NULL UNIQUE REFERENCES clusters(id),
                    l1_label VARCHAR(255),
                    l2_label VARCHAR(255),
                    l1_id INTEGER,
                    l2_id INTEGER,
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)

            # Phase 4: Classification corrections (human feedback)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS classification_corrections (
                    id SERIAL PRIMARY KEY,
                    publication_id BIGINT NOT NULL,
                    assigned_cluster_id INTEGER NOT NULL REFERENCES clusters(id),
                    correct_cluster_id INTEGER NOT NULL REFERENCES clusters(id),
                    corrected_by VARCHAR(255),
                    confidence DOUBLE PRECISION,
                    timestamp TIMESTAMP DEFAULT NOW()
                );
            """)

            # Phase 4: Cluster metrics (quality and performance indicators)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cluster_metrics (
                    id SERIAL PRIMARY KEY,
                    cluster_id INTEGER NOT NULL UNIQUE REFERENCES clusters(id),
                    intra_cluster_mean_similarity DOUBLE PRECISION,
                    member_count INTEGER,
                    correction_rate_30d DOUBLE PRECISION,
                    pending_inflow_rate DOUBLE PRECISION,
                    centroid_drift DOUBLE PRECISION,
                    last_label_updated_at TIMESTAMP,
                    exemplar_coverage DOUBLE PRECISION,
                    computed_at TIMESTAMP DEFAULT NOW()
                );
            """)

            # Structured per-run audit log (gap G3)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS clustering_run_log (
                    id                  SERIAL PRIMARY KEY,
                    started_at          TIMESTAMP NOT NULL,
                    finished_at         TIMESTAMP NOT NULL,
                    duration_seconds    DOUBLE PRECISION,
                    total_publications  INTEGER,
                    clusters_before     INTEGER,
                    clusters_after      INTEGER,
                    new_clusters        INTEGER,
                    id_matches_reused   INTEGER,
                    noise_points        INTEGER,
                    pending_before      INTEGER,
                    pending_after       INTEGER
                );
            """)

            # Phase 4: Dynamic Configuration Panel
            cur.execute("""
                CREATE TABLE IF NOT EXISTS system_config (
                    key VARCHAR(100) PRIMARY KEY,
                    value VARCHAR(255) NOT NULL,
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)

            conn.commit()
            print("Database initialized: pgvector extension enabled, tables created.")
    finally:
        conn.close()


def log_clustering_run(
    started_at,
    finished_at,
    total_publications: int,
    clusters_before: int,
    clusters_after: int,
    new_clusters: int,
    id_matches_reused: int,
    noise_points: int,
    pending_before: int,
    pending_after: int,
) -> None:
    """
    Persist a structured audit record for one HDBSCAN recluster run.

    Args:
        started_at: datetime when the run started.
        finished_at: datetime when the run finished.
        total_publications: total embeddings processed.
        clusters_before: number of clusters before this run.
        clusters_after: number of clusters after this run.
        new_clusters: clusters assigned a new UUID (not matched to any old cluster).
        id_matches_reused: clusters that reused a stable ID from the previous run.
        noise_points: publications labelled -1 by HDBSCAN.
        pending_before: size of the pending pool before this run.
        pending_after: size of the pending pool after this run.
    """
    import logging as _logging
    _logger = _logging.getLogger(__name__)
    duration = (finished_at - started_at).total_seconds()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO clustering_run_log (
                    started_at, finished_at, duration_seconds,
                    total_publications,
                    clusters_before, clusters_after,
                    new_clusters, id_matches_reused,
                    noise_points,
                    pending_before, pending_after
                ) VALUES (
                    %(started_at)s, %(finished_at)s, %(duration)s,
                    %(total_publications)s,
                    %(clusters_before)s, %(clusters_after)s,
                    %(new_clusters)s, %(id_matches_reused)s,
                    %(noise_points)s,
                    %(pending_before)s, %(pending_after)s
                );
                """,
                dict(
                    started_at=started_at,
                    finished_at=finished_at,
                    duration=duration,
                    total_publications=total_publications,
                    clusters_before=clusters_before,
                    clusters_after=clusters_after,
                    new_clusters=new_clusters,
                    id_matches_reused=id_matches_reused,
                    noise_points=noise_points,
                    pending_before=pending_before,
                    pending_after=pending_after,
                ),
            )
            conn.commit()
            _logger.info(
                "Clustering run logged: %.1fs | pubs=%d | clusters %d->%d "
                "(+%d new, %d reused) | noise=%d | pending %d->%d",
                duration, total_publications,
                clusters_before, clusters_after,
                new_clusters, id_matches_reused,
                noise_points, pending_before, pending_after,
            )
    except Exception as exc:
        _logger.warning("Failed to write clustering run log: %s", exc)
    finally:
        conn.close()


def store_embedding(publication_id: int, embedding: list[float]):
    """
    Store or update the embedding for a publication.

    Args:
        publication_id: The publication's ID from the main database.
        embedding: The embedding vector.
    """
    conn = get_connection()
    register_vector_safely(conn)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO publication_embeddings (publication_id, embedding)
                VALUES (%s, %s::vector)
                ON CONFLICT (publication_id)
                DO UPDATE SET embedding = EXCLUDED.embedding;
            """, (publication_id, embedding))
            conn.commit()
    finally:
        conn.close()


def get_nearest_cluster(embedding: list[float]) -> tuple[int, str, float, float | None] | None:
    """
    Get the nearest cluster centroid and its similarity.

    Returns:
        Tuple of (cluster_id, label, similarity, cluster_tightness) or None.
    """
    assert_l2_normalized(embedding)
    conn = get_connection()
    register_vector_safely(conn)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, label, cluster_tightness, 1 - (centroid <=> %s::vector) AS similarity
                FROM clusters
                WHERE centroid IS NOT NULL
                ORDER BY centroid <=> %s::vector ASC
                LIMIT 1;
            """, (embedding, embedding))

            row = cur.fetchone()
            if row is None:
                return None

            cluster_id, label, cluster_tightness, similarity = row
            return (cluster_id, label, float(similarity), cluster_tightness)
    finally:
        conn.close()


def get_top_k_clusters(embedding: list[float], k: int = 3) -> list[tuple[int, str, float, float | None]]:
    """
    Get top-K nearest cluster centroids and their similarities.
    Returns list of (cluster_id, label, similarity, cluster_tightness).
    """
    assert_l2_normalized(embedding)
    conn = get_connection()
    register_vector_safely(conn)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, label, cluster_tightness, 1 - (centroid <=> %s::vector) AS similarity
                FROM clusters
                WHERE centroid IS NOT NULL
                ORDER BY centroid <=> %s::vector ASC
                LIMIT %s;
            """, (embedding, embedding, max(1, k)))
            rows = cur.fetchall()
            return [
                (row[0], row[1], float(row[3]), row[2])
                for row in rows
            ]
    finally:
        conn.close()


def find_nearest_cluster(embedding: list[float], threshold: float) -> tuple[int, str, float] | None:
    """
    Find the nearest cluster centroid using cosine distance.

    Args:
        embedding: The query embedding vector.
        threshold: Minimum cosine similarity (1 - cosine_distance) required.

    Returns:
        Tuple of (cluster_id, label, similarity) if a match is found, else None.
    """
    result = get_nearest_cluster(embedding)
    if result is None:
        return None
    cluster_id, label, similarity, _ = result
    if similarity >= threshold:
        return (cluster_id, label, similarity)
    return None

def find_nearest_centroid_for_outlier(embedding: list[float], soft_threshold: float) -> tuple[int, str, float] | None:
    """
    Find the nearest cluster centroid using a softer threshold for UI suggestions.
    Returns (cluster_id, label, similarity) or None.
    """
    assert_l2_normalized(embedding)
    conn = get_connection()
    register_vector_safely(conn)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, label, 1 - (centroid <=> %s::vector) AS similarity
                FROM clusters
                WHERE centroid IS NOT NULL
                ORDER BY centroid <=> %s::vector ASC
                LIMIT 1;
            """, (embedding, embedding))

            row = cur.fetchone()
            if row is None:
                return None

            cluster_id, label, similarity = row
            if similarity >= soft_threshold:
                return (cluster_id, label, float(similarity))
            return None
    finally:
        conn.close()


def create_cluster(centroid: list[float], label: str) -> int:
    """
    Create a new cluster with the given centroid and label.

    Args:
        centroid: The centroid vector for the new cluster.
        label: The auto-generated cluster label.

    Returns:
        The new cluster's ID.
    """
    assert_l2_normalized(centroid)
    conn = get_connection()
    register_vector_safely(conn)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO clusters (label, centroid, member_count)
                VALUES (%s, %s::vector, 1)
                RETURNING id;
            """, (label, centroid))
            cluster_id = cur.fetchone()[0]
            conn.commit()
            return cluster_id
    finally:
        conn.close()


def update_cluster_centroid(cluster_id: int):
    """
    Recalculate the cluster centroid as the average of all member embeddings,
    and update the member count.

    Args:
        cluster_id: The cluster to update.
    """
    conn = get_connection()
    register_vector_safely(conn)
    try:
        with conn.cursor() as cur:
            # Calculate average embedding of all publications in this cluster
            cur.execute("""
                UPDATE clusters
                SET centroid = sub.avg_embedding,
                    member_count = sub.cnt,
                    updated_at = NOW()
                FROM (
                    SELECT
                        AVG(pe.embedding) AS avg_embedding,
                        COUNT(*) AS cnt
                    FROM publication_embeddings pe
                    JOIN publications p ON p.id = pe.publication_id
                    WHERE p.cluster_id = %s
                ) sub
                WHERE clusters.id = %s;
            """, (cluster_id, cluster_id))
            conn.commit()
    finally:
        conn.close()


def update_cluster_centroid_running_mean(cluster_id: int, new_embedding: list[float]) -> None:
    """
    Update the cluster centroid using a numerically correct running mean.

    Args:
        cluster_id: The cluster to update.
        new_embedding: The new member's embedding (L2-normalized).
    """
    assert_l2_normalized(new_embedding)
    conn = get_connection()
    register_vector_safely(conn)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT centroid, member_count
                FROM clusters
                WHERE id = %s;
            """, (cluster_id,))
            row = cur.fetchone()
            if row is None:
                return

            centroid, member_count = row
            member_count = int(member_count or 0)

            if centroid is None or member_count == 0:
                new_centroid = new_embedding
                new_count = 1
            else:
                centroid_list = centroid.tolist() if hasattr(centroid, "tolist") else list(centroid)
                new_count = member_count + 1
                new_centroid = [
                    (centroid_list[i] * member_count + new_embedding[i]) / new_count
                    for i in range(len(new_embedding))
                ]

            cur.execute("""
                UPDATE clusters
                SET centroid = %s::vector,
                    member_count = %s,
                    updated_at = NOW()
                WHERE id = %s;
            """, (new_centroid, new_count, cluster_id))
            conn.commit()
    finally:
        conn.close()


def update_cluster_tightness(cluster_id: int, new_tightness: float) -> None:
    """
    Update cluster_tightness (used for adaptive thresholds).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE clusters
                SET cluster_tightness = %s,
                    updated_at = NOW()
                WHERE id = %s;
            """, (new_tightness, cluster_id))
            conn.commit()
    finally:
        conn.close()


def update_publication_cluster(publication_id: int, cluster_id: int, cluster_label: str,
                               suggested_cluster_id: int | None = None, 
                               suggested_cluster_label: str | None = None):
    """
    Update the cluster_id and cluster_label on the publications table.

    Args:
        publication_id: The publication to update.
        cluster_id: The assigned cluster ID.
        cluster_label: The cluster's label.
        suggested_cluster_id: Fallback soft-assigned cluster.
        suggested_cluster_label: Fallback soft-assigned label.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE publications
                SET cluster_id = %s, cluster_label = %s,
                    suggested_cluster_id = %s, suggested_cluster_label = %s
                WHERE id = %s;
            """, (cluster_id, cluster_label, suggested_cluster_id, suggested_cluster_label, publication_id))
            conn.commit()
    except psycopg2.errors.UndefinedColumn:
        # Graceful fallback if Java hasn't run the migration yet for the suggested columns
        conn.rollback()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE publications
                SET cluster_id = %s, cluster_label = %s
                WHERE id = %s;
            """, (cluster_id, cluster_label, publication_id))
            conn.commit()
    finally:
        conn.close()


def get_all_clusters() -> list[dict]:
    """Get all clusters with their metadata."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT id AS cluster_id, label, member_count
                FROM clusters
                ORDER BY member_count DESC;
            """)
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def get_cluster_detail(cluster_id: int) -> dict | None:
    """Get cluster details including member publication IDs."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Cluster info
            cur.execute("""
                SELECT id AS cluster_id, label, member_count
                FROM clusters WHERE id = %s;
            """, (cluster_id,))
            cluster = cur.fetchone()
            if cluster is None:
                return None

            # Member publication IDs
            cur.execute("""
                SELECT id FROM publications
                WHERE cluster_id = %s
                ORDER BY id;
            """, (cluster_id,))
            pub_ids = [row["id"] for row in cur.fetchall()]

            result = dict(cluster)
            result["publication_ids"] = pub_ids
            return result
    finally:
        conn.close()


def get_existing_clusters() -> list[dict]:
    """Load existing clusters with centroids for stable ID matching."""
    conn = get_connection()
    register_vector_safely(conn)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT id, label, centroid, cluster_tightness
                FROM clusters
                WHERE centroid IS NOT NULL
                ORDER BY id;
            """)
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def get_all_embeddings() -> list[tuple[int, list[float], datetime | None, int]]:
    """Load all publication embeddings for batch re-clustering."""
    conn = get_connection()
    register_vector_safely(conn)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT publication_id, embedding, pending_since, COALESCE(recluster_attempts, 0)
                FROM publication_embeddings;
            """)
            return [
                (
                    row[0],
                    row[1].tolist() if hasattr(row[1], "tolist") else list(row[1]),
                    row[2],
                    int(row[3] or 0),
                )
                for row in cur.fetchall()
            ]
    finally:
        conn.close()


def set_publication_pending(publication_id: int, suggested_cluster_id: int | None = None) -> None:
    """Mark a publication embedding as pending for reclustering and log inflow event."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE publication_embeddings
                SET pending_since = NOW(),
                    recluster_attempts = 0
                WHERE publication_id = %s;
            """, (publication_id,))
            cur.execute("""
                INSERT INTO pending_inflow_events (publication_id, suggested_cluster_id, created_at)
                VALUES (%s, %s, NOW());
            """, (publication_id, suggested_cluster_id))
            conn.commit()
    finally:
        conn.close()


def clear_publication_pending(publication_id: int) -> None:
    """Clear pending status for a publication embedding."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE publication_embeddings
                SET pending_since = NULL,
                    recluster_attempts = 0
                WHERE publication_id = %s;
            """, (publication_id,))
            conn.commit()
    finally:
        conn.close()


def get_pending_pool_count() -> int:
    """Count publications in the pending pool."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*)
                FROM publication_embeddings
                WHERE pending_since IS NOT NULL;
            """)
            return int(cur.fetchone()[0])
    finally:
        conn.close()


def get_clustering_state() -> tuple[datetime | None, int]:
    """Get last clustering run state."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT last_run_at, last_publication_count
                FROM clustering_state
                WHERE id = 1;
            """)
            row = cur.fetchone()
            if row is None:
                cur.execute("""
                    INSERT INTO clustering_state (id, last_publication_count)
                    VALUES (1, 0)
                    ON CONFLICT (id) DO NOTHING;
                """)
                conn.commit()
                return None, 0
            return row[0], int(row[1] or 0)
    finally:
        conn.close()


def update_clustering_state(last_run_at: datetime, last_publication_count: int) -> None:
    """Update last clustering run state."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE clustering_state
                SET last_run_at = %s,
                    last_publication_count = %s
                WHERE id = 1;
            """, (last_run_at, last_publication_count))
            conn.commit()
    finally:
        conn.close()


def record_cluster_lineage(mappings: list[tuple[int | None, int, float]]) -> None:
    """Record cluster lineage mappings."""
    if not mappings:
        return
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.executemany("""
                INSERT INTO cluster_lineage (old_cluster_id, new_cluster_id, similarity_score, matched_at)
                VALUES (%s, %s, %s, NOW());
            """, mappings)
            conn.commit()
    finally:
        conn.close()


def reset_clusters():
    """Delete all clusters and reset cluster assignments on publications."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            try:
                cur.execute("UPDATE publications SET cluster_id = NULL, cluster_label = NULL, suggested_cluster_id = NULL, suggested_cluster_label = NULL;")
            except psycopg2.errors.UndefinedColumn:
                conn.rollback()
                cur.execute("UPDATE publications SET cluster_id = NULL, cluster_label = NULL;")
            # Use TRUNCATE CASCADE to clear clusters and all dependent tables (metrics, hierarchy, exemplars)
            cur.execute("TRUNCATE TABLE clusters CASCADE;")
            conn.commit()
    finally:
        conn.close()


def bulk_update_clusters(cluster_assignments: dict[int, dict], cluster_info: dict[int, dict]):
    """
    Bulk update cluster assignments after re-clustering.

    Args:
        cluster_assignments: {publication_id: {"cluster_id": int, "suggested_cluster_id": int|None,
                                              "pending_since": datetime|None, "recluster_attempts": int}}
        cluster_info: {cluster_id: {"label": str, "centroid": list[float], "count": int, "tightness": float}}
    """
    conn = get_connection()
    register_vector_safely(conn)
    try:
        with conn.cursor() as cur:
            # Clear existing clusters
            cur.execute("DELETE FROM clusters;")
            # Try to reset all cluster IDs and suggested fields
            try:
                cur.execute("UPDATE publications SET cluster_id = NULL, cluster_label = NULL, suggested_cluster_id = NULL, suggested_cluster_label = NULL;")
            except psycopg2.errors.UndefinedColumn:
                conn.rollback()
                cur.execute("UPDATE publications SET cluster_id = NULL, cluster_label = NULL;")

            # Insert new clusters
            for cid, info in cluster_info.items():
                cur.execute("""
                    INSERT INTO clusters (id, label, centroid, cluster_tightness, member_count, created_at, updated_at)
                    VALUES (%s, %s, %s::vector, %s, %s, NOW(), NOW());
                """, (cid, info["label"], info["centroid"], info.get("tightness"), info["count"]))

            # Update publications
            for pub_id, assignment_data in cluster_assignments.items():
                cid = assignment_data.get("cluster_id")
                suggested_cid = assignment_data.get("suggested_cluster_id")
                pending_since = assignment_data.get("pending_since")
                recluster_attempts = int(assignment_data.get("recluster_attempts") or 0)

                if cid != -1 and cid in cluster_info:
                    label = cluster_info[cid]["label"]
                elif pending_since:
                    label = "Pending / Unconfirmed"
                else:
                    label = "Others / Unclustered"
                suggested_label = cluster_info[suggested_cid]["label"] if suggested_cid and suggested_cid in cluster_info else None

                try:
                    cur.execute("""
                        UPDATE publications 
                        SET cluster_id = %s, cluster_label = %s,
                            suggested_cluster_id = %s, suggested_cluster_label = %s
                        WHERE id = %s;
                    """, (cid, label, suggested_cid, suggested_label, pub_id))
                except psycopg2.errors.UndefinedColumn:
                    conn.rollback()
                    cur.execute("""
                        UPDATE publications 
                        SET cluster_id = %s, cluster_label = %s
                        WHERE id = %s;
                    """, (cid, label, pub_id))

                cur.execute("""
                    UPDATE publication_embeddings
                    SET pending_since = %s,
                        recluster_attempts = %s
                    WHERE publication_id = %s;
                """, (pending_since, recluster_attempts, pub_id))

            # Reset sequence to max cluster id
            if cluster_info:
                max_id = max(cluster_info.keys())
                cur.execute(f"SELECT setval('clusters_id_seq', {max_id});")

            conn.commit()
    finally:
        conn.close()

def get_total_publication_count() -> int:
    """Gets total number of publications."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM publications;")
            return cur.fetchone()[0]
    finally:
        conn.close()

def try_advisory_lock() -> bool:
    """Attempt to acquire a Postgres advisory lock to prevent concurrent clustering jobs."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 8675309 is an arbitrary 64-bit integer lock ID
            cur.execute("SELECT pg_try_advisory_lock(8675309);")
            return cur.fetchone()[0]
    finally:
        conn.close()

def unlock_advisory_lock():
    """Release the advisory lock."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_unlock(8675309);")
            conn.commit()
    finally:
        conn.close()


# ============================================================================
# PHASE 3: Exemplars and Domain Priors
# ============================================================================

def refresh_cluster_exemplars(cluster_info: dict[int, list[int]]) -> None:
    """
    Refresh exemplars for clusters. Called after HDBSCAN finishes.
    
    Exemplars are the K papers closest to each cluster centroid (K = 5% of cluster size,
    min 3, max 50).
    
    Args:
        cluster_info: {cluster_id: [publication_ids]} mapping.
    """
    conn = get_connection()
    register_vector_safely(conn)
    try:
        with conn.cursor() as cur:
            # Clear old exemplars
            cur.execute("DELETE FROM cluster_exemplars;")
            
            for cluster_id, pub_ids in cluster_info.items():
                if not pub_ids:
                    continue
                
                # Compute K = 5% of cluster size (min 3, max 50)
                k = max(3, min(50, int(len(pub_ids) * 0.05)))
                
                # Fetch embeddings and centroid
                cur.execute("""
                    SELECT centroid FROM clusters WHERE id = %s;
                """, (cluster_id,))
                row = cur.fetchone()
                if not row:
                    continue
                
                centroid = row[0]
                if isinstance(centroid, str):
                    # pgvector returns as string; parse it
                    import json
                    centroid = json.loads(centroid.replace('[', '[').replace(']', ']'))
                elif hasattr(centroid, 'tolist'):
                    centroid = centroid.tolist()
                else:
                    centroid = list(centroid)
                
                # Fetch embeddings for this cluster's publications
                cur.execute("""
                    SELECT publication_id, embedding
                    FROM publication_embeddings
                    WHERE publication_id = ANY(%s);
                """, (pub_ids,))
                
                exemplars = []
                for pub_id, emb in cur.fetchall():
                    if hasattr(emb, 'tolist'):
                        emb_list = emb.tolist()
                    else:
                        emb_list = list(emb)
                    
                    # Compute cosine distance to centroid
                    import numpy as np
                    from sklearn.metrics.pairwise import cosine_similarity
                    
                    dist = float(1.0 - cosine_similarity([emb_list], [centroid])[0, 0])
                    exemplars.append((pub_id, dist))
                
                # Sort by distance (closest first) and take top K
                exemplars.sort(key=lambda x: x[1])
                top_exemplars = exemplars[:k]
                
                # Insert exemplars
                for rank, (pub_id, dist) in enumerate(top_exemplars):
                    cur.execute("""
                        INSERT INTO cluster_exemplars (cluster_id, publication_id, distance_to_centroid, exemplar_rank)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (cluster_id, publication_id) DO UPDATE
                        SET distance_to_centroid = %s, exemplar_rank = %s, updated_at = NOW();
                    """, (cluster_id, pub_id, dist, rank, dist, rank))
            
            conn.commit()
    finally:
        conn.close()


def get_cluster_exemplars(cluster_id: int) -> list[tuple[int, float]]:
    """
    Fetch exemplars for a cluster (publication_id, distance_to_centroid).
    
    Args:
        cluster_id: Cluster ID.
    
    Returns:
        List of (publication_id, distance) tuples, sorted by exemplar_rank.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT publication_id, distance_to_centroid
                FROM cluster_exemplars
                WHERE cluster_id = %s
                ORDER BY exemplar_rank ASC;
            """, (cluster_id,))
            return [(int(row[0]), float(row[1])) for row in cur.fetchall()]
    finally:
        conn.close()


def set_cluster_domain_prior(cluster_id: int, dominant_domain: str | None, confidence: float) -> None:
    """
    Store the dominant domain for a cluster.
    
    Args:
        cluster_id: Cluster ID.
        dominant_domain: Domain name or None if no dominant domain.
        confidence: Confidence score (0–1).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO cluster_domain_prior (cluster_id, dominant_domain, confidence, updated_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (cluster_id) DO UPDATE
                SET dominant_domain = %s, confidence = %s, updated_at = NOW();
            """, (cluster_id, dominant_domain, confidence, dominant_domain, confidence))
            conn.commit()
    finally:
        conn.close()


def get_cluster_domain_prior(cluster_id: int) -> tuple[str | None, float] | None:
    """
    Fetch the dominant domain for a cluster.
    
    Args:
        cluster_id: Cluster ID.
    
    Returns:
        (dominant_domain, confidence) or None if not set.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT dominant_domain, confidence
                FROM cluster_domain_prior
                WHERE cluster_id = %s;
            """, (cluster_id,))
            row = cur.fetchone()
            if row:
                return (row[0], float(row[1]))
            return None
    finally:
        conn.close()


def get_cluster_label_keywords(cluster_id: int) -> tuple[str | None, list[str] | None]:
    """
    Fetch cluster label and keywords.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT label, keywords
                FROM clusters
                WHERE id = %s;
            """, (cluster_id,))
            row = cur.fetchone()
            if row:
                return row[0], row[1]
            return None, None
    finally:
        conn.close()


def update_cluster_label_and_description(
    cluster_id: int,
    label: str,
    description: str | None = None,
    keywords: list[str] | None = None
) -> None:
    """
    Update cluster label, description, and keywords.
    
    Args:
        cluster_id: Cluster ID.
        label: New cluster label (generated by Gemma).
        description: Optional description.
        keywords: Optional list of keywords.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    UPDATE clusters
                    SET label = %s,
                        description = %s,
                        keywords = %s,
                        updated_at = NOW()
                    WHERE id = %s;
                """, (label, description, keywords, cluster_id))
                conn.commit()
            except psycopg2.errors.UndefinedColumn:
                conn.rollback()
                cur.execute("""
                    UPDATE clusters
                    SET label = %s, updated_at = NOW()
                    WHERE id = %s;
                """, (label, cluster_id))
                conn.commit()
    finally:
        conn.close()


def get_cluster_member_publication_ids(cluster_id: int) -> list[int]:
    """
    Fetch all publication IDs for a cluster.
    
    Args:
        cluster_id: Cluster ID.
    
    Returns:
        List of publication IDs.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id FROM publications WHERE cluster_id = %s;
            """, (cluster_id,))
            return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


# ============================================================================
# PHASE 4: Hierarchy, Corrections, and Metrics
# ============================================================================

def insert_or_update_cluster_hierarchy(cluster_id: int, l1_label: str | None, l2_label: str | None, 
                                       l1_id: int | None, l2_id: int | None) -> None:
    """
    Insert or update cluster hierarchy (L1/L2 classification).
    
    Args:
        cluster_id: Cluster ID.
        l1_label: Level 1 (top-level) category label.
        l2_label: Level 2 (sub-category) label.
        l1_id: Level 1 category ID.
        l2_id: Level 2 category ID.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO cluster_hierarchy (cluster_id, l1_label, l2_label, l1_id, l2_id, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (cluster_id) DO UPDATE
                SET l1_label = %s, l2_label = %s, l1_id = %s, l2_id = %s, updated_at = NOW();
            """, (cluster_id, l1_label, l2_label, l1_id, l2_id, l1_label, l2_label, l1_id, l2_id))
            conn.commit()
    finally:
        conn.close()


def get_cluster_hierarchy(cluster_id: int) -> dict | None:
    """
    Fetch cluster hierarchy.
    
    Args:
        cluster_id: Cluster ID.
    
    Returns:
        Dictionary with l1_label, l2_label, l1_id, l2_id, updated_at or None if not found.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT l1_label, l2_label, l1_id, l2_id, updated_at
                FROM cluster_hierarchy
                WHERE cluster_id = %s;
            """, (cluster_id,))
            row = cur.fetchone()
            if row:
                return {
                    "l1_label": row[0],
                    "l2_label": row[1],
                    "l1_id": row[2],
                    "l2_id": row[3],
                    "updated_at": row[4]
                }
            return None
    finally:
        conn.close()


def insert_classification_correction(publication_id: int, assigned_cluster_id: int, 
                                     correct_cluster_id: int, corrected_by: str | None = None,
                                     confidence: float | None = None) -> None:
    """
    Record a classification correction (human feedback).
    
    Args:
        publication_id: Publication ID.
        assigned_cluster_id: Cluster ID that was assigned by the algorithm.
        correct_cluster_id: Cluster ID that the user corrected to.
        corrected_by: Username or identifier of the corrector.
        confidence: Optional confidence score (0-1) for the correction.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO classification_corrections 
                (publication_id, assigned_cluster_id, correct_cluster_id, corrected_by, confidence, timestamp)
                VALUES (%s, %s, %s, %s, %s, NOW());
            """, (publication_id, assigned_cluster_id, correct_cluster_id, corrected_by, confidence))
            conn.commit()
    finally:
        conn.close()


def get_recent_corrections(days: int = 30, limit: int = 1000) -> list[dict]:
    """
    Fetch recent classification corrections.
    
    Args:
        days: Number of days to look back (default 30).
        limit: Maximum number of corrections to return (default 1000).
    
    Returns:
        List of correction dictionaries with publication_id, assigned_cluster_id, correct_cluster_id, etc.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT publication_id, assigned_cluster_id, correct_cluster_id, corrected_by, confidence, timestamp
                FROM classification_corrections
                WHERE timestamp >= NOW() - (%s * INTERVAL '1 day')
                ORDER BY timestamp DESC
                LIMIT %s;
            """, (days, limit))
            
            return [
                {
                    "publication_id": row[0],
                    "assigned_cluster_id": row[1],
                    "correct_cluster_id": row[2],
                    "corrected_by": row[3],
                    "confidence": float(row[4]) if row[4] is not None else None,
                    "timestamp": row[5]
                }
                for row in cur.fetchall()
            ]
    finally:
        conn.close()


def insert_or_update_cluster_metrics(cluster_id: int, intra_cluster_mean_similarity: float | None = None,
                                     member_count: int | None = None, correction_rate_30d: float | None = None,
                                     pending_inflow_rate: float | None = None, centroid_drift: float | None = None,
                                     last_label_updated_at: datetime | None = None, exemplar_coverage: float | None = None) -> None:
    """
    Insert or update cluster metrics (quality indicators).
    
    Args:
        cluster_id: Cluster ID.
        intra_cluster_mean_similarity: Mean cosine similarity between all member pairs.
        member_count: Number of members in cluster.
        correction_rate_30d: Proportion of corrected classifications in last 30 days.
        pending_inflow_rate: Rate of pending (unconfirmed) assignments per day.
        centroid_drift: Euclidean distance of centroid from previous iteration.
        last_label_updated_at: Timestamp when cluster label was last updated.
        exemplar_coverage: Percentage of cluster members covered by exemplars.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO cluster_metrics 
                (cluster_id, intra_cluster_mean_similarity, member_count, correction_rate_30d,
                 pending_inflow_rate, centroid_drift, last_label_updated_at, exemplar_coverage, computed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (cluster_id) DO UPDATE
                SET intra_cluster_mean_similarity = COALESCE(%s, cluster_metrics.intra_cluster_mean_similarity),
                    member_count = COALESCE(%s, cluster_metrics.member_count),
                    correction_rate_30d = COALESCE(%s, cluster_metrics.correction_rate_30d),
                    pending_inflow_rate = COALESCE(%s, cluster_metrics.pending_inflow_rate),
                    centroid_drift = COALESCE(%s, cluster_metrics.centroid_drift),
                    last_label_updated_at = COALESCE(%s, cluster_metrics.last_label_updated_at),
                    exemplar_coverage = COALESCE(%s, cluster_metrics.exemplar_coverage),
                    computed_at = NOW();
            """, (cluster_id, intra_cluster_mean_similarity, member_count, correction_rate_30d,
                  pending_inflow_rate, centroid_drift, last_label_updated_at, exemplar_coverage,
                  intra_cluster_mean_similarity, member_count, correction_rate_30d,
                  pending_inflow_rate, centroid_drift, last_label_updated_at, exemplar_coverage))
            conn.commit()
    finally:
        conn.close()


def get_pending_inflow_rates(days: int = 1) -> dict[int, float]:
    """
    Compute pending inflow rate per cluster based on pending_inflow_events.

    Args:
        days: Lookback window in days (default 1).

    Returns:
        Dict of {cluster_id: pending_inflow_rate_per_day}.
    """
    if days <= 0:
        return {}
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT suggested_cluster_id, COUNT(*)
                FROM pending_inflow_events
                WHERE created_at >= NOW() - (%s * INTERVAL '1 day')
                  AND suggested_cluster_id IS NOT NULL
                GROUP BY suggested_cluster_id;
            """, (days,))
            rates = {}
            for cluster_id, count in cur.fetchall():
                rates[int(cluster_id)] = float(count) / float(days)
            return rates
    finally:
        conn.close()


def get_cluster_metrics(cluster_id: int) -> dict | None:
    """
    Fetch cluster metrics.
    
    Args:
        cluster_id: Cluster ID.
    
    Returns:
        Dictionary with all metric fields or None if not found.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT intra_cluster_mean_similarity, member_count, correction_rate_30d,
                       pending_inflow_rate, centroid_drift, last_label_updated_at,
                       exemplar_coverage, computed_at
                FROM cluster_metrics
                WHERE cluster_id = %s;
            """, (cluster_id,))
            row = cur.fetchone()
            if row:
                return {
                    "intra_cluster_mean_similarity": float(row[0]) if row[0] is not None else None,
                    "member_count": row[1],
                    "correction_rate_30d": float(row[2]) if row[2] is not None else None,
                    "pending_inflow_rate": float(row[3]) if row[3] is not None else None,
                    "centroid_drift": float(row[4]) if row[4] is not None else None,
                    "last_label_updated_at": row[5],
                    "exemplar_coverage": float(row[6]) if row[6] is not None else None,
                    "computed_at": row[7]
                }
            return None
    finally:
        conn.close()


def get_all_cluster_metrics(order_by: str = "computed_at", descending: bool = True) -> list[dict]:
    """
    Fetch metrics for all clusters.
    
    Args:
        order_by: Column to order by (e.g., 'correction_rate_30d', 'centroid_drift').
        descending: If True, order DESC, else ASC.
    
    Returns:
        List of metric dictionaries with cluster_id included.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            allowed_columns = {
                "cluster_id",
                "intra_cluster_mean_similarity",
                "member_count",
                "correction_rate_30d",
                "pending_inflow_rate",
                "centroid_drift",
                "last_label_updated_at",
                "exemplar_coverage",
                "computed_at",
            }
            safe_order_by = order_by if order_by in allowed_columns else "computed_at"
            order_dir = "DESC" if descending else "ASC"
            query = f"""
                SELECT cluster_id, intra_cluster_mean_similarity, member_count, correction_rate_30d,
                       pending_inflow_rate, centroid_drift, last_label_updated_at,
                       exemplar_coverage, computed_at
                FROM cluster_metrics
                ORDER BY {safe_order_by} {order_dir};
            """
            cur.execute(query)
            
            return [
                {
                    "cluster_id": row[0],
                    "intra_cluster_mean_similarity": float(row[1]) if row[1] is not None else None,
                    "member_count": row[2],
                    "correction_rate_30d": float(row[3]) if row[3] is not None else None,
                    "pending_inflow_rate": float(row[4]) if row[4] is not None else None,
                    "centroid_drift": float(row[5]) if row[5] is not None else None,
                    "last_label_updated_at": row[6],
                    "exemplar_coverage": float(row[7]) if row[7] is not None else None,
                    "computed_at": row[8]
                }
                for row in cur.fetchall()
            ]
    finally:
        conn.close()



def get_clustering_run_log(limit: int = 20) -> list[dict]:
    """
    Fetch recent HDBSCAN run audit records, newest first.

    Args:
        limit: Maximum rows to return.

    Returns:
        List of dicts matching ClusteringRunLogEntry schema.
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    id,
                    started_at, finished_at, duration_seconds,
                    total_publications,
                    clusters_before, clusters_after,
                    new_clusters, id_matches_reused,
                    noise_points,
                    pending_before, pending_after
                FROM clustering_run_log
                ORDER BY started_at DESC
                LIMIT %(limit)s;
                """,
                {"limit": limit},
            )
            result = []
            for row in cur.fetchall():
                # Convert datetime to ISO string
                row["started_at"] = row["started_at"].isoformat()
                row["finished_at"] = row["finished_at"].isoformat()
                result.append(row)
            return result
    finally:
        conn.close()


def upsert_system_config(key: str, value: str) -> None:
    """
    Insert or update a system configuration key-value pair.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO system_config (key, value, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (key) DO UPDATE 
                SET value = EXCLUDED.value, updated_at = NOW();
            """, (key, str(value)))
            conn.commit()
    finally:
        conn.close()


def get_recent_corrections(page: int = 0, page_size: int = 20) -> list[dict]:
    """
    Get recent classification corrections.
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    id,
                    publication_id,
                    assigned_cluster_id,
                    correct_cluster_id,
                    corrected_by,
                    confidence,
                    timestamp
                FROM classification_corrections
                ORDER BY timestamp DESC
                LIMIT %s OFFSET %s;
            """, (page_size, page * page_size))
            result = []
            for row in cur.fetchall():
                row["timestamp"] = row["timestamp"].isoformat()
                result.append(row)
            return result
    finally:
        conn.close()
