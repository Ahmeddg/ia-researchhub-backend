import json
import logging
from typing import List
import numpy as np
import psycopg2
from app.config import settings

DATABASE_URL = settings.DATABASE_URL
logger = logging.getLogger(__name__)

def recommend_personalized(upvoted_ids: List[int], downvoted_ids: List[int], top_k: int = 1000):
    """
    Enhanced recommendation using Hybrid Max-Similarity + Domain Boosting.
    - No longer neglects any publication (removed NOT IN filter).
    - Downvoted publications have their score decreased (multiplied by 0.1).
    - Upvoted publications or similar ones have their score increased.
    - Supports Cold-Start and includes publications without embeddings via LEFT JOIN.
    """
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                up_ids_tuple = tuple(upvoted_ids) if upvoted_ids else (-1,)
                down_ids_tuple = tuple(downvoted_ids) if downvoted_ids else (-1,)

                if not upvoted_ids:
                    logger.info("No upvotes. Using default score with downvote penalty.")
                    sim_sql = "0.5"
                    params = []
                else:
                    # Get upvoted vectors
                    cur.execute("SELECT embedding FROM publication_embeddings WHERE publication_id IN %s", (up_ids_tuple,))
                    upvoted_vectors = [np.array(row[0]) for row in cur.fetchall()]
                    
                    # Get upvoted domain IDs
                    cur.execute("SELECT domain_id FROM publications WHERE id IN %s", (up_ids_tuple,))
                    domains = set(row[0] for row in cur.fetchall() if row[0] is not None)
                    upvoted_domain_tuple = tuple(domains) if domains else (-1,)
                    
                    if not upvoted_vectors:
                        logger.info("Upvoted IDs found but no embeddings yet. Using default score.")
                        sim_sql = "0.5"
                        params = []
                    else:
                        sim_exprs = [f"(COALESCE(1 - (e.embedding <=> %s::vector), 0.0))" for _ in upvoted_vectors]
                        # Interaction match (1.0) OR (best vector match + domain boost)
                        sim_sql = f"""
                            GREATEST(
                                CASE WHEN p.id IN %s THEN 1.0 ELSE 0.0 END,
                                GREATEST({', '.join(sim_exprs)}) + 
                                CASE WHEN p.domain_id IN %s THEN 0.3 ELSE 0.0 END
                            )
                        """
                        params = [up_ids_tuple] + upvoted_vectors + [upvoted_domain_tuple]

                # Apply downvote penalty: match * 0.1 if downvoted, else match * 1.0
                final_score_sql = f"({sim_sql}) * (CASE WHEN p.id IN %s THEN 0.1 ELSE 1.0 END)"
                params.append(down_ids_tuple)
                params.append(top_k)

                query = f"""
                    SELECT p.id, {final_score_sql} as final_score
                    FROM publications p
                    LEFT JOIN publication_embeddings e ON p.id = e.publication_id
                    WHERE p.status = 'PUBLISHED'
                    ORDER BY final_score DESC, p.publication_date DESC, p.id DESC
                    LIMIT %s
                """
                cur.execute(query, params)
                results = [{"publication_id": r[0], "similarity_score": float(r[1])} for r in cur.fetchall()]
                
                logger.info(f"Generated {len(results)} personalized recommendations for user.")
                return results
    except Exception as e:
        logger.error(f"Error in recommend_personalized: {e}")
        return []

def recommend_similar_publications(publication_id: int, top_k: int = 5):
    """Finds top_k publications similar to a target publication_id."""
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT embedding FROM publication_embeddings WHERE publication_id = %s", (publication_id,))
                row = cur.fetchone()
                if not row: return []
                target_vector = row[0]
                query = """
                    SELECT publication_id, 1 - (embedding <=> %s::vector) as score 
                    FROM publication_embeddings 
                    WHERE publication_id != %s 
                    ORDER BY score DESC LIMIT %s
                """
                cur.execute(query, (target_vector, publication_id, top_k))
                return [{"publication_id": r[0], "similarity_score": float(r[1])} for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error in recommend_similar: {e}"); return []

def recommend_with_cluster_filter(publication_id: int, cluster_id: int, top_k: int = 5):
    """Recommendation strictly within the same cluster."""
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT embedding FROM publication_embeddings WHERE publication_id = %s", (publication_id,))
                row = cur.fetchone()
                if not row: return []
                target_vector = row[0]
                query = """
                    SELECT e.publication_id, 1 - (e.embedding <=> %s::vector) as score 
                    FROM publication_embeddings e
                    JOIN publications p ON e.publication_id = p.id
                    WHERE e.publication_id != %s AND p.cluster_id = %s
                    ORDER BY score DESC LIMIT %s
                """
                cur.execute(query, (target_vector, publication_id, cluster_id, top_k))
                return [{"publication_id": r[0], "similarity_score": float(r[1])} for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error in recommend_cluster: {e}"); return []

def detect_close_pairs(threshold: float = 0.95):
    """Detects near-duplicate articles."""
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT a.publication_id, b.publication_id, 1 - (a.embedding <=> b.embedding) as score
                    FROM publication_embeddings a
                    JOIN publication_embeddings b ON a.publication_id < b.publication_id
                    WHERE 1 - (a.embedding <=> b.embedding) > %s
                    ORDER BY score DESC LIMIT 50
                """
                cur.execute(query, (threshold,))
                return [{"id1": r[0], "id2": r[1], "score": float(r[2])} for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error in detect_close_pairs: {e}"); return []
