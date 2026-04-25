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
    MODEL_NAME: str = os.getenv("MODEL_NAME", "all-MiniLM-L6-v2")
    EMBEDDING_DIM: int = 384  # Dimension of all-MiniLM-L6-v2 output

    # Clustering
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.75"))
    SOFT_SIMILARITY_THRESHOLD: float = float(os.getenv("SOFT_SIMILARITY_THRESHOLD", "0.65"))
    HDBSCAN_MIN_CLUSTER_SIZE: int = int(os.getenv("HDBSCAN_MIN_CLUSTER_SIZE", "5"))

    # Ollama / Gemma 3 Integration
    OLLAMA_API_URL: str = os.getenv("OLLAMA_API_URL", "https://api.ollama.com/api/generate")
    OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "28de8464911240dc9b29591a0c97bf12.XcaV7bc7kZnrTnqwfMHuxR66")
    OLLAMA_MODEL_NAME: str = os.getenv("OLLAMA_MODEL_NAME", "gemma3:4b-cloud")

    # Service
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

settings = Settings()
