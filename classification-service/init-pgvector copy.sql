-- Initialize pgvector extension and classification tables
-- This script is run automatically when the PostgreSQL container starts

CREATE EXTENSION IF NOT EXISTS vector;

-- Store publication embeddings (768 dimensions for SPECTER2)
CREATE TABLE IF NOT EXISTS publication_embeddings (
    publication_id BIGINT PRIMARY KEY,
    embedding vector(768) NOT NULL,
    pending_since TIMESTAMP,
    recluster_attempts INTEGER DEFAULT 0
);

-- Store cluster centroids and metadata
CREATE TABLE IF NOT EXISTS clusters (
    id SERIAL PRIMARY KEY,
    label VARCHAR(200),
    centroid vector(768),
    cluster_tightness DOUBLE PRECISION,
    member_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Cluster lineage audit table
CREATE TABLE IF NOT EXISTS cluster_lineage (
    id SERIAL PRIMARY KEY,
    old_cluster_id INTEGER,
    new_cluster_id INTEGER NOT NULL,
    similarity_score DOUBLE PRECISION,
    matched_at TIMESTAMP DEFAULT NOW()
);

-- Clustering run state table
CREATE TABLE IF NOT EXISTS clustering_state (
    id INTEGER PRIMARY KEY,
    last_run_at TIMESTAMP,
    last_publication_count INTEGER DEFAULT 0
);

INSERT INTO clustering_state (id, last_publication_count)
VALUES (1, 0)
ON CONFLICT (id) DO NOTHING;

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

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'publications' AND column_name = 'suggested_cluster_id'
    ) THEN
        ALTER TABLE publications ADD COLUMN suggested_cluster_id INTEGER;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'publications' AND column_name = 'suggested_cluster_label'
    ) THEN
        ALTER TABLE publications ADD COLUMN suggested_cluster_label VARCHAR(200);
    END IF;
END $$;
