import psycopg2
import json

DB_URL = "postgresql://postgres:password@127.0.0.1:5433/article_db"

def audit():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # 1. List Tables
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        tables = [t[0] for t in cur.fetchall()]
        print(f"Tables: {tables}")
        
        # 2. Check Publications state
        cur.execute("SELECT COUNT(*) FROM publications")
        pub_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM publications WHERE cluster_id IS NULL")
        missing_clusters = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM publications WHERE ai_categories IS NULL OR ai_categories = ''")
        missing_categories = cur.fetchone()[0]
        
        # 3. Check Embeddings state
        cur.execute("SELECT COUNT(*) FROM publication_embeddings")
        embedding_count = cur.fetchone()[0]
        
        # 4. Check Domains distribution
        cur.execute("""
            SELECT d.name, COUNT(p.id) 
            FROM domains d 
            LEFT JOIN publications p ON d.id = p.domain_id 
            GROUP BY d.name
        """)
        domain_dist = cur.fetchall()
        
        # 5. Check Votes
        cur.execute("SELECT COUNT(*) FROM publication_votes")
        vote_count = cur.fetchone()[0]
        
        # 6. Check columns for key tables
        audit_results = {
            "summary": {
                "total_publications": pub_count,
                "publications_with_embeddings": embedding_count,
                "missing_ai_clusters": missing_clusters,
                "missing_ai_categories": missing_categories,
                "total_votes": vote_count
            },
            "domain_distribution": {name: count for name, count in domain_dist},
            "tables_structure": {}
        }
        
        for table in tables:
            cur.execute(f"SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name='{table}'")
            audit_results["tables_structure"][table] = [{"name": c[0], "type": c[1], "null": c[2]} for c in cur.fetchall()]
            
        print(json.dumps(audit_results, indent=2))
        
    except Exception as e:
        print(f"Audit failed: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    audit()
