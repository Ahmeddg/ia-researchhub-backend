"""
Embedding generation using sentence-transformers.
Loads the model once at module level and provides a function to generate embeddings.
"""

import math
from sentence_transformers import SentenceTransformer
from app.config import settings

# Global model instance — loaded once at startup
_model: SentenceTransformer | None = None


def load_model() -> SentenceTransformer:
    """Load the sentence-transformer model. Called once at app startup."""
    global _model
    if _model is None:
        print(f"Loading embedding model: {settings.MODEL_NAME}...")
        _model = SentenceTransformer(settings.MODEL_NAME)
        print("Model loaded successfully.")
    return _model


def is_model_loaded() -> bool:
    """Check if the model has been loaded."""
    return _model is not None


def assert_l2_normalized(embedding: list[float] | object, tolerance: float = 1e-3) -> None:
    """
    Ensure embeddings are L2-normalized before any distance computation.
    """
    squared_sum = 0.0
    for value in embedding:
        squared_sum += float(value) ** 2
    norm = math.sqrt(squared_sum)
    if abs(norm - 1.0) > tolerance:
        raise ValueError(f"Embedding is not L2-normalized (norm={norm:.6f}).")


def get_embedding(text: str) -> list[float]:
    """
    Generate a 768-dimensional embedding vector from text.

    Args:
        text: The input text (abstract, title, or combined).

    Returns:
        A list of floats representing the embedding vector.
    """
    model = load_model()
    embedding = model.encode(text, normalize_embeddings=True)
    assert_l2_normalized(embedding)
    return embedding.tolist()


def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a batch of texts (more efficient than one-by-one).

    Args:
        texts: List of input texts.

    Returns:
        List of embedding vectors.
    """
    model = load_model()
    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32)
    for embedding in embeddings:
        assert_l2_normalized(embedding)
    return [e.tolist() for e in embeddings]
