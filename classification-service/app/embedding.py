"""
Embedding generation using sentence-transformers.
Loads the model once at module level and provides a function to generate embeddings.
"""

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


def get_embedding(text: str) -> list[float]:
    """
    Generate a 384-dimensional embedding vector from text.

    Args:
        text: The input text (abstract, title, or combined).

    Returns:
        A list of floats representing the embedding vector.
    """
    model = load_model()
    embedding = model.encode(text, normalize_embeddings=True)
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
    return [e.tolist() for e in embeddings]
