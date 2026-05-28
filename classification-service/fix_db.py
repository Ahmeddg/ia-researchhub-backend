import psycopg2
from app.config import settings

def fix_schema():
    print("Connecting to DB:", settings.DATABASE_URL)
    conn = psycopg2.connect(settings.DATABASE_URL)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            # Drop indexes first
            cur.execute("DROP INDEX IF EXISTS idx_pub_embeddings_embedding;")
            cur.execute("DROP INDEX IF EXISTS idx_clusters_centroid;")
            
            # Truncate tables to remove 384-dim data (cascades to all dependent cluster tables)
            print("Truncating old 384-dimensional data...")
            cur.execute("TRUNCATE TABLE publication_embeddings;")
            cur.execute("TRUNCATE TABLE clusters CASCADE;")
            
            # Alter column types
            print("Altering column types to vector(768)...")
            cur.execute("ALTER TABLE publication_embeddings ALTER COLUMN embedding TYPE vector(768);")
            cur.execute("ALTER TABLE clusters ALTER COLUMN centroid TYPE vector(768);")
            
            # Recreate indexes
            print("Recreating IVFFlat indexes...")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_pub_embeddings_embedding ON publication_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_clusters_centroid ON clusters USING ivfflat (centroid vector_cosine_ops) WITH (lists = 50);")
            
            print("Database schema successfully updated to 768 dimensions.")
    except Exception as e:
        print("Error:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    fix_schema()
