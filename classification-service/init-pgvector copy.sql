-- Initialize pgvector extension and classification tables
-- This script is run automatically when the PostgreSQL container starts

CREATE EXTENSION IF NOT EXISTS vector;

-- Store publication embeddings (384 dimensions for all-MiniLM-L6-v2)
CREATE TABLE IF NOT EXISTS publication_embeddings (
    publication_id BIGINT PRIMARY KEY,
    embedding vector(384) NOT NULL
);

-- Store cluster centroids and metadata
CREATE TABLE IF NOT EXISTS clusters (
    id SERIAL PRIMARY KEY,
    label VARCHAR(200),
    centroid vector(384),
    member_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Add cluster columns to publications table (if not present)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'publications' AND column_name = 'cluster_id'
    ) THEN
        ALTER TABLE publications ADD COLUMN cluster_id INTEGER;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'publications' AND column_name = 'cluster_label'
    ) THEN
        ALTER TABLE publications ADD COLUMN cluster_label VARCHAR(200);
    END IF;
END $$;
