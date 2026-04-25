"""
Database operations for pgvector-powered classification.
Manages the publication_embeddings and clusters tables.
"""

import psycopg2
import psycopg2.extras
from pgvector.psycopg2 import register_vector
from app.config import settings


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
                    centroid vector({settings.EMBEDDING_DIM}),
                    member_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)

            conn.commit()
            print("Database initialized: pgvector extension enabled, tables created.")
    finally:
        conn.close()


def store_embedding(publication_id: int, embedding: list[float]):
    """
    Store or update the embedding for a publication.

    Args:
        publication_id: The publication's ID from the main database.
        embedding: The 384-dim embedding vector.
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


def find_nearest_cluster(embedding: list[float], threshold: float) -> tuple[int, str, float] | None:
    """
    Find the nearest cluster centroid using cosine distance.

    Args:
        embedding: The query embedding vector.
        threshold: Minimum cosine similarity (1 - cosine_distance) required.

    Returns:
        Tuple of (cluster_id, label, similarity) if a match is found, else None.
    """
    conn = get_connection()
    register_vector_safely(conn)
    try:
        with conn.cursor() as cur:
            # cosine distance: <=> operator. Similarity = 1 - distance.
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
            if similarity >= threshold:
                return (cluster_id, label, float(similarity))
            return None
    finally:
        conn.close()

def find_nearest_centroid_for_outlier(embedding: list[float], soft_threshold: float) -> tuple[int, str, float] | None:
    """
    Find the nearest cluster centroid using a softer threshold for UI suggestions.
    Returns (cluster_id, label, similarity) or None.
    """
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


def get_all_embeddings() -> list[tuple[int, list[float]]]:
    """Load all publication embeddings for batch re-clustering."""
    conn = get_connection()
    register_vector_safely(conn)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT publication_id, embedding FROM publication_embeddings;")
            return [(row[0], row[1].tolist() if hasattr(row[1], 'tolist') else list(row[1]))
                    for row in cur.fetchall()]
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
            cur.execute("DELETE FROM clusters;")
            conn.commit()
    finally:
        conn.close()


def bulk_update_clusters(cluster_assignments: dict[int, int], cluster_info: dict[int, dict]):
    """
    Bulk update cluster assignments after re-clustering.

    Args:
        cluster_assignments: {publication_id: cluster_id}
        cluster_info: {cluster_id: {"label": str, "centroid": list[float], "count": int}}
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
                    INSERT INTO clusters (id, label, centroid, member_count, created_at, updated_at)
                    VALUES (%s, %s, %s::vector, %s, NOW(), NOW());
                """, (cid, info["label"], info["centroid"], info["count"]))

            # Update publications
            for pub_id, assignment_data in cluster_assignments.items():
                cid = assignment_data.get("cluster_id")
                suggested_cid = assignment_data.get("suggested_cluster_id")
                
                label = cluster_info[cid]["label"] if cid != -1 and cid in cluster_info else "Uncategorized"
                suggested_label = cluster_info[suggested_cid]["label"] if suggested_cid and suggested_cid in cluster_info else None
                
                if cid == -1:
                    cid = None
                    label = None

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
