"""
Clustering logic: assigns publications to clusters based on embedding similarity.
Uses TF-IDF keyword extraction for automatic cluster label generation.
Combines title + abstract + extracted PDF text for richer embeddings.
"""

import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from app.config import settings
from app.embedding import get_embedding
from app.pdf_extractor import extract_text_from_pdf_url
from app.llm import generate_categories_and_keywords, LLMClassificationResult
from app.db import (
    store_embedding,
    find_nearest_cluster,
    find_nearest_centroid_for_outlier,
    create_cluster,
    update_cluster_centroid,
    update_publication_cluster,
)

logger = logging.getLogger(__name__)


def generate_cluster_label(title: str, abstract_text: str, domain: str | None = None) -> str:
    """
    Generate a human-readable cluster label from the publication text
    using TF-IDF keyword extraction.

    Args:
        title: Publication title.
        abstract_text: Publication abstract.
        domain: Optional domain name for context.

    Returns:
        A short label string like "Deep Learning in Medical Imaging".
    """
    combined_text = f"{title}. {abstract_text}"

    try:
        # Use TF-IDF to find the most important terms
        vectorizer = TfidfVectorizer(
            max_features=10,
            stop_words="english",
            ngram_range=(1, 2),  # Unigrams and bigrams
            min_df=1,
        )
        vectorizer.fit_transform([combined_text])
        keywords = vectorizer.get_feature_names_out()

        # Build a label from the top 3 keywords
        top_keywords = list(keywords[:3])
        label = " & ".join(kw.title() for kw in top_keywords)

        # Prepend domain if available and not already in the label
        if domain and domain.lower() not in label.lower():
            label = f"{domain}: {label}"

        # Ensure label isn't too long
        if len(label) > 100:
            label = label[:97] + "..."

        return label

    except Exception:
        # Fallback: use first words of the title
        words = title.split()[:4]
        return " ".join(words)


def generate_batch_cluster_label(texts: list[str]) -> str:
    """
    Generate a cluster label from multiple publication texts.
    Used during re-clustering when we have all member texts.

    Args:
        texts: List of combined title+abstract texts for cluster members.

    Returns:
        A short label string.
    """
    try:
        vectorizer = TfidfVectorizer(
            max_features=20,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()

        # Sum TF-IDF scores across all documents for each term
        scores = tfidf_matrix.sum(axis=0).A1
        top_indices = scores.argsort()[-3:][::-1]
        top_keywords = [feature_names[i] for i in top_indices]

        label = " & ".join(kw.title() for kw in top_keywords)
        if len(label) > 100:
            label = label[:97] + "..."
        return label

    except Exception:
        return "Uncategorized"


def _build_clean_text(title: str, abstract_text: str,
                     pdf_url: str | None = None) -> str:
    """
    Build the combined input text for embedding generation.
    clean_text = title + abstract + extracted PDF (first 2-3 pages).

    Args:
        title: Publication title.
        abstract_text: Publication abstract.
        pdf_url: Optional URL to the PDF file.

    Returns:
        Tuple of (clean_text, pdf_text)
    """
    parts = [title]
    pdf_text = ""

    if abstract_text:
        parts.append(abstract_text)

    # Extract text from the first 2-3 pages of the PDF
    if pdf_url:
        logger.info(f"Extracting PDF text for richer embedding: {pdf_url}")
        pdf_text = extract_text_from_pdf_url(pdf_url)
        if pdf_text:
            parts.append(pdf_text)
            logger.info(f"PDF extraction added {len(pdf_text)} characters")
        else:
            logger.info("PDF extraction returned no text, using title + abstract only")

    clean_text = ". ".join(parts)
    return clean_text, pdf_text


def assign_cluster(publication_id: int, title: str, abstract_text: str,
                   domain: str | None = None,
                   pdf_url: str | None = None) -> tuple[int, str, float, LLMClassificationResult]:
    """
    Assign a publication to a cluster. This is the main classification entry point.

    Steps:
        1. Build clean_text = title + abstract + PDF (first 2-3 pages)
        2. Generate embedding from clean_text
        3. Store embedding in publication_embeddings table
        4. Call Gemma 3 LLM to get predicted categories and keywords
        5. Find nearest cluster centroid (cosine similarity >= threshold)
        6. If match: assign to existing cluster, update centroid
        7. If no match: create new cluster with this embedding as centroid

    Args:
        publication_id: The publication's database ID.
        title: Publication title.
        abstract_text: Publication abstract text.
        domain: Optional domain name for label generation.
        pdf_url: Optional URL of the PDF for text extraction (first 2-3 pages).

    Returns:
        Tuple of (cluster_id, cluster_label, confidence, LLMClassificationResult, suggested_cluster_id, suggested_cluster_label).
    """
    # Combine title + abstract + extracted PDF text
    clean_text, pdf_text = _build_clean_text(title, abstract_text, pdf_url)
    embedding = get_embedding(clean_text)

    # Call LLM for categories and keywords
    llm_result = generate_categories_and_keywords(title, abstract_text, pdf_text)

    # Store the embedding
    store_embedding(publication_id, embedding)

    # Try to find an existing cluster
    result = find_nearest_cluster(embedding, settings.SIMILARITY_THRESHOLD)

    if result is not None:
        cluster_id, cluster_label, similarity = result

        # Assign publication to this cluster
        update_publication_cluster(publication_id, cluster_id, cluster_label)

        # Recalculate cluster centroid with the new member
        update_cluster_centroid(cluster_id)

        return (cluster_id, cluster_label, similarity, llm_result, None, None)

    else:
        # No strict match found; try soft match for UI suggestion
        soft_result = find_nearest_centroid_for_outlier(embedding, settings.SOFT_SIMILARITY_THRESHOLD)
        suggested_id, suggested_label = None, None
        
        if soft_result is not None:
            suggested_id, suggested_label, _ = soft_result
            
        # Treat as outlier since strict match failed. Let HDBSCAN create actual new clusters.
        cluster_id = -1
        label = "Others / Unclustered"

        # Update publication with outlier status + suggestion
        update_publication_cluster(publication_id, cluster_id, label, suggested_id, suggested_label)

        return (cluster_id, label, 0.0, llm_result, suggested_id, suggested_label)
