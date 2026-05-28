# Classification Service — Technical Report
### IAResearchHub · Automatic Scientific Publication Classification

---

## 1. Overview

The **Classification Service** is a Python microservice (FastAPI + uvicorn) that automatically organises scientific publications into thematic research clusters. When a new article is submitted, the service embeds its content, places it into the most semantically similar cluster, and updates live quality metrics — all without human intervention.

The service sits behind a Spring Boot backend that proxies requests from the Angular frontend.

```
Angular (UI) ──► Spring Boot (Port 8081) ──► FastAPI (Port 8001) ──► PostgreSQL + pgvector
```

---

## 2. Core Technologies

| Component | Technology | Role |
|---|---|---|
| Embedding model | **SPECTER2** (`allenai/specter2_base`) | Convert paper text into a semantic vector |
| Vector database | **PostgreSQL + pgvector** | Store & query embeddings with cosine similarity |
| Incremental clustering | **Centroid-based k-NN** | Assign new papers to existing clusters |
| Full re-clustering | **HDBSCAN** | Rediscover clusters from scratch on a schedule |
| Taxonomy hierarchy | **CAH (Ward linkage, scipy)** | Build a 2-level topic tree over cluster centroids |
| Label generation | **Gemma 3 (LLM)** | Give human-readable names to clusters and taxonomy nodes |
| API framework | **FastAPI** | REST endpoints consumed by Spring Boot |

---

## 3. Step-by-Step: What Happens When a New Publication is Added

### Step 1 — Text Preparation
The service builds a **rich input text** by concatenating:
- The paper's **title**
- The paper's **abstract**
- The first 2–3 pages of text extracted from the **PDF** (if a URL is provided)

```python
clean_text = title + ". " + abstract + ". " + pdf_first_pages
```

Using more than just the title/abstract makes the embedding far more semantically precise.

---

### Step 2 — Generating the Embedding (SPECTER2)
The combined text is passed through **SPECTER2**, a transformer model fine-tuned specifically on scientific papers (titles + abstracts from Semantic Scholar). It outputs a **fixed-size dense vector** (768 dimensions) that captures the semantic meaning of the paper.

The vector is then **L2-normalised** (divided by its own magnitude), so all vectors lie on the surface of a unit hypersphere. This makes **cosine similarity** equivalent to a simple dot product, which is faster and more numerically stable.

```python
embedding = model.encode(clean_text)
embedding = embedding / np.linalg.norm(embedding)  # L2 normalise
```

The embedding is stored in the `publication_embeddings` table (powered by **pgvector**).

---

### Step 3 — LLM Keyword Extraction (Gemma 3)
In parallel, **Gemma 3** is called to extract a short list of **domain keywords** from the title and abstract. These keywords are used later to compute an **Explainability Score** — a measure of how well the assigned cluster actually matches the paper's content.

---

### Step 4 — Finding Candidate Clusters (pgvector k-NN)
The service queries pgvector for the **top-3 clusters** whose centroid is closest to the paper's embedding, using cosine similarity:

```sql
SELECT id, label, cluster_tightness,
       1 - (centroid <=> %s::vector) AS similarity
FROM clusters
ORDER BY centroid <=> %s::vector
LIMIT 3;
```

The `<=>` operator is pgvector's cosine distance. This query runs in sub-millisecond time even with thousands of clusters thanks to pgvector's HNSW index.

---

### Step 5 — Dynamic Similarity Threshold
For each candidate cluster, a **dynamic threshold** is computed based on that cluster's **tightness** (how similar its members are to each other):

```
dynamic_threshold = clamp(tightness × multiplier, MIN_THRESHOLD, MAX_THRESHOLD)
```

A tight cluster (members all very similar to each other) demands a **higher similarity** before accepting a new member. A loose cluster (more diverse topic) is more permissive. This prevents tight, specialised clusters from being polluted with tangential papers.

---

### Step 6 — Exemplar-Based Verification (k-NN Second Pass)
Rather than trusting only the cluster centroid, the service also computes the similarity to the cluster's **exemplars** — the K papers closest to the centroid that best represent the cluster's core topic. This is a mini k-NN pass that guards against centroid drift errors.

```
exemplar_similarity = mean(cosine_similarity(paper_embedding, exemplar_embedding)
                           for each exemplar)
```

---

### Step 7 — Domain Prior Boost
If the paper's declared **domain** (e.g., "Computer Vision") matches the dominant domain of a candidate cluster, the similarity score is boosted by **+0.05**. This is a lightweight Bayesian prior — if the declared field matches, it's more likely to belong there.

---

### Step 8 — Assignment Decision

Using the adjusted similarity score, one of three outcomes is reached:

| Condition | Outcome |
|---|---|
| `adjusted_similarity >= dynamic_threshold` | ✅ **Assigned** to the best cluster |
| `adjusted_similarity >= SOFT_THRESHOLD` | ⏳ **Pending / Unconfirmed** — soft-assigned, awaits confirmation |
| `adjusted_similarity < SOFT_THRESHOLD` | ❌ **Others / Unclustered** — outlier, queued for next re-clustering |

---

### Step 9 — Cluster Update (Running Mean Centroid)
When a paper is successfully assigned, the cluster's **centroid is updated online** using a numerically correct running mean — without loading all member embeddings:

```
new_centroid = (old_centroid × N + new_embedding) / (N + 1)
```

This keeps the centroid accurate as the cluster grows, at O(1) cost per paper. The `clusters.member_count` and `cluster_metrics.member_count` are also updated in the same database transaction.

---

### Step 10 — Explainability Score
A final **Explainability Score** is returned to the caller:

```
score = |paper_keywords ∩ cluster_keywords| / |paper_keywords ∪ cluster_keywords|
```

This is a **Jaccard similarity** between the paper's LLM-extracted keywords and the cluster's stored keywords. A score close to 1.0 means the cluster label closely matches what the paper is about. It lets researchers audit why a paper was placed in a given cluster.

---

## 4. Periodic Full Re-Clustering (HDBSCAN)

Every night (or when a configurable trigger fires), the service runs a **full re-cluster** of all publications using **HDBSCAN** (Hierarchical Density-Based Spatial Clustering of Applications with Noise).

### Why HDBSCAN?
- **No need to pre-specify the number of clusters** — it discovers them automatically from the data density.
- **Noise-robust** — papers that don't fit any cluster are labelled as noise (-1) rather than forced into a wrong cluster.
- **Handles variable-density clusters** — scientific literature naturally has some very dense subfields and some sparse ones.

### Re-Clustering Steps
1. Load all L2-normalised embeddings from `publication_embeddings`.
2. Run HDBSCAN with `metric='euclidean'` (equivalent to cosine on L2-normalised vectors), `min_cluster_size` from config.
3. Use the **Hungarian algorithm** (`scipy.optimize.linear_sum_assignment`) to **match new clusters to old clusters** by centroid similarity — this preserves cluster IDs across runs so the frontend stays consistent.
4. For each new cluster: generate a label using Gemma 3 (sampling the 5–10 papers closest to the centroid).
5. Recompute all **cluster metrics** (tightness, drift, exemplar coverage, correction rate).
6. Run the **CAH taxonomy** step (see Section 5).

---

## 5. Taxonomy: CAH (Clustering After Hierarchy)

After HDBSCAN produces the leaf clusters, a second layer of **Hierarchical Agglomerative Clustering (CAH)** is applied — but this time on the **cluster centroids** (not on individual papers). This produces a 2-level taxonomy tree:

```
L1 (Broad field)       — e.g., "Computer Vision Networks"
  └─ L2 (Sub-area)     — e.g., "ImageNet-Based Networks"
       └─ Leaf Cluster  — e.g., "Transformer-Based Vision and Language Models" (5 docs)
```

### Algorithm
1. Collect the centroid vectors of all HDBSCAN clusters.
2. Compute pairwise **Euclidean distances** between centroids (valid for L2-normalised vectors).
3. Apply **Ward linkage** (`scipy.cluster.hierarchy.linkage(distances, method='ward')`), which minimises within-cluster variance at each merge step.
4. Cut the dendrogram at two heights:
   - **L1 cut** → `CAH_L1_COUNT` broad categories (default 3–5)
   - **L2 cut** → `CAH_L2_COUNT` sub-categories (default 6–10)
5. **Gemma 3** then reads the leaf cluster labels under each L1/L2 node and generates a human-readable taxonomy label asynchronously in a background thread (so it doesn't block the re-cluster response).

The hierarchy is stored in the `cluster_hierarchy` table and exposed via `GET /taxonomy`.

---

## 6. Quality Metrics (Per Cluster)

The `cluster_metrics` table tracks the health of each cluster:

| Metric | Formula | Meaning |
|---|---|---|
| **Intra-cluster mean similarity** | Mean pairwise cosine sim. of all members | How coherent / tight the cluster is |
| **Member count** | Count of publications in cluster | Size |
| **Correction rate (30d)** | `corrections_in_30d / member_count` | How often humans override the AI assignment |
| **Pending inflow rate** | Pending papers per day | Backpressure from new papers not yet confirmed |
| **Centroid drift** | `1 - cosine_similarity(old_centroid, new_centroid)` | How much the cluster's meaning has shifted |
| **Exemplar coverage** | `exemplars / member_count` | What fraction of the cluster is "explained" by representative papers |

These metrics are displayed in the **AI Ops → System Health** dashboard and used to colour-code clusters as 🟢 STABLE, 🟡 AMBER, or 🔴 RED.

---

## 7. Human-in-the-Loop: Corrections Queue

A human expert can **correct** a classification via the Corrections Queue tab. When a correction is submitted:
1. The correction is recorded in the `classification_corrections` table.
2. The paper's exemplar status is updated — it becomes a **seeded exemplar** for the correct cluster.
3. On the next re-cluster, HDBSCAN will respect these seeded exemplars, pulling the cluster boundary in the right direction.

This creates a **feedback loop**: the more corrections experts make, the better the automatic assignments become over time.

---

## 8. Dynamic Configuration

All key clustering parameters are stored in the `system_config` PostgreSQL table and can be changed at runtime from the **Configuration** tab without restarting the service:

| Parameter | Default | Effect |
|---|---|---|
| `SIMILARITY_THRESHOLD` | 0.72 | Minimum cosine similarity to assign a paper |
| `SOFT_SIMILARITY_THRESHOLD` | 0.55 | Below this → outlier; above → pending |
| `HDBSCAN_MIN_CLUSTER_SIZE` | 5 | Minimum papers to form a new cluster |
| `CAH_L1_COUNT` | 4 | Number of broad taxonomy categories |
| `CAH_L2_COUNT` | 8 | Number of taxonomy sub-categories |

---

## 9. Architecture Summary (Data Flow)

```
New Publication
     │
     ▼
[1] Build text = title + abstract + PDF pages
     │
     ▼
[2] SPECTER2 → 768-dim L2-normalised embedding
     │
     ├──► store in publication_embeddings (pgvector)
     │
     ▼
[3] pgvector k-NN → top-3 candidate clusters
     │
     ▼
[4] For each candidate:
    ├── compute dynamic threshold (from cluster tightness)
    ├── compute exemplar similarity (k-NN second pass)
    └── apply domain prior boost (+0.05)
     │
     ▼
[5] Decision:
    ├── similarity ≥ threshold  → ASSIGN to cluster
    ├── similarity ≥ soft limit → PENDING / Unconfirmed
    └── below soft limit        → OUTLIER / Unclustered
     │
     ▼  (if ASSIGNED)
[6] Update cluster centroid (running mean, O(1))
    Sync cluster_metrics.member_count
    Compute Explainability Score (Jaccard)
     │
     ▼
[7] Nightly: HDBSCAN re-cluster all publications
    ► Hungarian matching (preserve IDs)
    ► Gemma 3 cluster naming
    ► CAH taxonomy (Ward linkage on centroids)
    ► Gemma 3 taxonomy labeling (async background)
    ► Recompute all metrics
```

---

## 10. Key Design Decisions & Justifications

**Why SPECTER2 instead of a general-purpose model like BERT?**
SPECTER2 is trained on citation graphs and paper metadata from Semantic Scholar. It understands scientific language and the semantic relationships between papers far better than a general NLP model. Two papers that cite the same body of work will have embeddings that are closer together.

**Why L2-normalise all embeddings?**
On the unit hypersphere, cosine similarity equals the dot product, which pgvector can compute extremely efficiently. It also means Euclidean distance is a monotone transformation of cosine distance, making Ward-linkage CAH valid on these vectors.

**Why a running-mean centroid instead of recomputing from scratch?**
Recomputing the centroid after every new paper would require loading all member embeddings — an O(N) read per insertion. The running mean is O(1): `new_centroid = (old × N + new) / (N+1)`.

**Why HDBSCAN instead of K-Means?**
K-Means requires you to specify the number of clusters K in advance and always forces every point into a cluster. Scientific literature does not divide neatly into a fixed number of topics. HDBSCAN discovers the number and shape of clusters automatically and can label outliers as noise.

**Why CAH on top of HDBSCAN?**
HDBSCAN gives leaf-level clusters (e.g., "U-Net segmentation papers"). CAH groups these leaves into a human-navigable hierarchy. The two-pass approach lets HDBSCAN handle the noisy, variable-density individual paper space while CAH handles the cleaner, lower-dimensional space of cluster centroids.
