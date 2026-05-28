"""
Configuration for the classification microservice.
All settings are loaded from environment variables with sensible defaults.
"""

import os


class Settings:
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5433/article_db"
    )

    # Embedding model
    # NOTE: allenai/specter2 is now an adapter; the base model is specter2_base.
    MODEL_NAME: str = os.getenv("MODEL_NAME", "allenai/specter2_base")
    EMBEDDING_DIM: int = 768  # Dimension of SPECTER2 output

    # Clustering
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.75"))
    SOFT_SIMILARITY_THRESHOLD: float = float(os.getenv("SOFT_SIMILARITY_THRESHOLD", "0.65"))
    HDBSCAN_MIN_CLUSTER_SIZE: int = int(os.getenv("HDBSCAN_MIN_CLUSTER_SIZE", "5"))
    STABLE_ID_SIMILARITY_THRESHOLD: float = float(os.getenv("STABLE_ID_SIMILARITY_THRESHOLD", "0.85"))
    DYNAMIC_THRESHOLD_MULTIPLIER: float = float(os.getenv("DYNAMIC_THRESHOLD_MULTIPLIER", "0.90"))
    MIN_ASSIGNMENT_THRESHOLD: float = float(os.getenv("MIN_ASSIGNMENT_THRESHOLD", "0.60"))
    MAX_ASSIGNMENT_THRESHOLD: float = float(os.getenv("MAX_ASSIGNMENT_THRESHOLD", "0.88"))
    PENDING_RECLUSTER_ATTEMPTS: int = int(os.getenv("PENDING_RECLUSTER_ATTEMPTS", "3"))
    RECLUSTER_MIN_NEW_PAPERS: int = int(os.getenv("RECLUSTER_MIN_NEW_PAPERS", "200"))
    RECLUSTER_PENDING_THRESHOLD: int = int(os.getenv("RECLUSTER_PENDING_THRESHOLD", "50"))
    RECLUSTER_MAX_INTERVAL_HOURS: int = int(os.getenv("RECLUSTER_MAX_INTERVAL_HOURS", "24"))

    # Phase 4: CAH (Clustering After Hierarchy) Configuration
    CAH_L1_COUNT: int = int(os.getenv("CAH_L1_COUNT", "8"))  # Target number of L1 clusters
    CAH_L2_COUNT: int = int(os.getenv("CAH_L2_COUNT", "30"))  # Target number of L2 clusters
    CORRECTION_WINDOW_DAYS: int = int(os.getenv("CORRECTION_WINDOW_DAYS", "30"))
    CORRECTION_RATE_HIGH: float = float(os.getenv("CORRECTION_RATE_HIGH", "0.10"))
    CORRECTION_RATE_LOW: float = float(os.getenv("CORRECTION_RATE_LOW", "0.02"))
    THRESHOLD_TIGHTEN_DELTA: float = float(os.getenv("THRESHOLD_TIGHTEN_DELTA", "0.02"))
    THRESHOLD_RELAX_DELTA: float = float(os.getenv("THRESHOLD_RELAX_DELTA", "0.01"))

    # Ollama / Gemma 3 Integration
    OLLAMA_API_URL: str = os.getenv("OLLAMA_API_URL", "https://api.ollama.com/api/generate")
    OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "28de8464911240dc9b29591a0c97bf12.XcaV7bc7kZnrTnqwfMHuxR66")
    OLLAMA_MODEL_NAME: str = os.getenv("OLLAMA_MODEL_NAME", "gemma3:4b-cloud")

    # Service
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

settings = Settings()
