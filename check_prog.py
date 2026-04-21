import psycopg2
conn = psycopg2.connect('postgresql://postgres:password@127.0.0.1:5433/article_db')
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM publications WHERE ai_categories IS NOT NULL AND ai_categories != ''")
print(f"Enriched: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM publications")
print(f"Total: {cur.fetchone()[0]}")
conn.close()
