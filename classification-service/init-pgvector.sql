-- Initialize pgvector extension and classification tables
-- This script is run automatically when the PostgreSQL container starts.
-- It is the canonical, complete schema — kept in sync with db.py / init_db().

CREATE EXTENSION IF NOT EXISTS vector;

-- ===========================================================================
-- CORE TABLES
-- ===========================================================================

-- Publication embeddings (768-dim SPECTER2 vectors)
CREATE TABLE IF NOT EXISTS publication_embeddings (
    publication_id     BIGINT PRIMARY KEY,
    embedding          vector(768) NOT NULL,
    pending_since      TIMESTAMP,
    recluster_attempts INTEGER DEFAULT 0
);

-- Cluster centroids and metadata
-- Includes Phase 3 columns: description, keywords
CREATE TABLE IF NOT EXISTS clusters (
    id                SERIAL PRIMARY KEY,
    label             VARCHAR(200),
    description       TEXT,
    keywords          TEXT[],
    centroid          vector(768),
    cluster_tightness DOUBLE PRECISION,
    member_count      INTEGER DEFAULT 0,
    created_at        TIMESTAMP DEFAULT NOW(),
    updated_at        TIMESTAMP DEFAULT NOW()
);

-- Cluster lineage audit table (Phase 2 — stable IDs)
CREATE TABLE IF NOT EXISTS cluster_lineage (
    id               SERIAL PRIMARY KEY,
    old_cluster_id   INTEGER,
    new_cluster_id   INTEGER NOT NULL,
    similarity_score DOUBLE PRECISION,
    matched_at       TIMESTAMP DEFAULT NOW()
);

-- Clustering run state (tracks last run time and publication count)
CREATE TABLE IF NOT EXISTS clustering_state (
    id                     INTEGER PRIMARY KEY,
    last_run_at            TIMESTAMP,
    last_publication_count INTEGER DEFAULT 0
);

INSERT INTO clustering_state (id, last_publication_count)
VALUES (1, 0)
ON CONFLICT (id) DO NOTHING;

-- ===========================================================================
-- PHASE 3 TABLES
-- ===========================================================================

-- K papers closest to each cluster centroid (exemplar-based kNN assignment)
CREATE TABLE IF NOT EXISTS cluster_exemplars (
    id                   SERIAL PRIMARY KEY,
    cluster_id           INTEGER NOT NULL REFERENCES clusters(id) ON DELETE CASCADE,
    publication_id       BIGINT  NOT NULL,
    distance_to_centroid DOUBLE PRECISION,
    exemplar_rank        INTEGER,
    updated_at           TIMESTAMP DEFAULT NOW(),
    UNIQUE (cluster_id, publication_id)
);

-- Dominant domain per cluster (soft domain prior in assignment)
CREATE TABLE IF NOT EXISTS cluster_domain_prior (
    cluster_id      INTEGER PRIMARY KEY REFERENCES clusters(id) ON DELETE CASCADE,
    dominant_domain VARCHAR(100),
    confidence      DOUBLE PRECISION,
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- Pending inflow events (for per-cluster inflow rate computation)
CREATE TABLE IF NOT EXISTS pending_inflow_events (
    id                   SERIAL PRIMARY KEY,
    publication_id       BIGINT NOT NULL,
    suggested_cluster_id INTEGER,
    created_at           TIMESTAMP DEFAULT NOW()
);

-- ===========================================================================
-- PHASE 4 TABLES
-- ===========================================================================

-- 3-level CAH taxonomy (L1 broad field / L2 subfield / L3 leaf cluster)
CREATE TABLE IF NOT EXISTS cluster_hierarchy (
    id         SERIAL PRIMARY KEY,
    cluster_id INTEGER NOT NULL UNIQUE REFERENCES clusters(id) ON DELETE CASCADE,
    l1_label   VARCHAR(255),
    l2_label   VARCHAR(255),
    l1_id      INTEGER,
    l2_id      INTEGER,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Human feedback / classification corrections
CREATE TABLE IF NOT EXISTS classification_corrections (
    id                  SERIAL PRIMARY KEY,
    publication_id      BIGINT  NOT NULL,
    assigned_cluster_id INTEGER NOT NULL REFERENCES clusters(id),
    correct_cluster_id  INTEGER NOT NULL REFERENCES clusters(id),
    corrected_by        VARCHAR(255),
    confidence          DOUBLE PRECISION,
    timestamp           TIMESTAMP DEFAULT NOW()
);

-- Per-cluster quality and performance metrics
CREATE TABLE IF NOT EXISTS cluster_metrics (
    id                            SERIAL PRIMARY KEY,
    cluster_id                    INTEGER NOT NULL UNIQUE REFERENCES clusters(id) ON DELETE CASCADE,
    intra_cluster_mean_similarity DOUBLE PRECISION,
    member_count                  INTEGER,
    correction_rate_30d           DOUBLE PRECISION,
    pending_inflow_rate           DOUBLE PRECISION,
    centroid_drift                DOUBLE PRECISION,
    last_label_updated_at         TIMESTAMP,
    exemplar_coverage             DOUBLE PRECISION,
    computed_at                   TIMESTAMP DEFAULT NOW()
);

-- ===========================================================================
-- PUBLICATIONS TABLE — add classification columns if missing
-- (The publications table itself is managed by the Spring Boot service)
-- ===========================================================================

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

-- ===========================================================================
-- PERFORMANCE INDEXES
-- ===========================================================================

-- ANN index on publication embeddings (cosine — matches HDBSCAN metric)
CREATE INDEX IF NOT EXISTS idx_pub_embeddings_embedding
    ON publication_embeddings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Pending pool queries (fast count / filter)
CREATE INDEX IF NOT EXISTS idx_pub_embeddings_pending
    ON publication_embeddings (pending_since)
    WHERE pending_since IS NOT NULL;

-- ANN index on cluster centroids (cosine — used by /classify top-K lookup)
CREATE INDEX IF NOT EXISTS idx_clusters_centroid
    ON clusters USING ivfflat (centroid vector_cosine_ops)
    WITH (lists = 50);

-- Exemplar lookups by cluster
CREATE INDEX IF NOT EXISTS idx_cluster_exemplars_cluster_id
    ON cluster_exemplars (cluster_id, exemplar_rank);

-- Correction history queries by cluster and time window
CREATE INDEX IF NOT EXISTS idx_corrections_assigned_cluster
    ON classification_corrections (assigned_cluster_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_corrections_correct_cluster
    ON classification_corrections (correct_cluster_id, timestamp DESC);

-- Pending inflow rate queries by cluster and time window
CREATE INDEX IF NOT EXISTS idx_pending_inflow_cluster_time
    ON pending_inflow_events (suggested_cluster_id, created_at DESC);

-- Publications cluster lookup
CREATE INDEX IF NOT EXISTS idx_publications_cluster_id
    ON publications (cluster_id);

-- HDBSCAN run audit log (gap G3)
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

CREATE INDEX IF NOT EXISTS idx_clustering_run_log_started
    ON clustering_run_log (started_at DESC);
