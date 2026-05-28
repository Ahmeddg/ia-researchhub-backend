"""
Clustering logic: assigns publications to clusters based on embedding similarity.
Uses Gemma for cluster naming and exemplar-based kNN assignment.
Incorporates domain as a soft prior.
"""

import logging
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.config import settings
from app.embedding import get_embedding
from app.pdf_extractor import extract_text_from_pdf_url
from app.llm import generate_keywords_for_paper, LLMClassificationResult
from app.db import (
    store_embedding,
    get_nearest_cluster,
    get_top_k_clusters,
    set_publication_pending,
    clear_publication_pending,
    update_cluster_centroid_running_mean,
    update_publication_cluster,
    get_cluster_exemplars,
    get_cluster_domain_prior,
    get_cluster_label_keywords,
)

logger = logging.getLogger(__name__)



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


def _compute_exemplar_similarity(embedding: list[float], exemplar_publication_ids: list[int]) -> float:
    """
    Compute average cosine similarity to exemplars (papers in cluster).
    
    Args:
        embedding: Publication embedding (L2-normalized).
        exemplar_publication_ids: List of exemplar publication IDs.
    
    Returns:
        Average similarity to exemplars.
    """
    if not exemplar_publication_ids:
        return 0.0
    
    try:
        from app.db import get_connection
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT embedding FROM publication_embeddings
                    WHERE publication_id = ANY(%s);
                """, (exemplar_publication_ids,))
                
                exemplar_sims = []
                for row in cur.fetchall():
                    emb = row[0]
                    if hasattr(emb, 'tolist'):
                        emb = emb.tolist()
                    else:
                        emb = list(emb)
                    
                    sim = float(cosine_similarity([embedding], [emb])[0, 0])
                    exemplar_sims.append(sim)
                
                return sum(exemplar_sims) / len(exemplar_sims) if exemplar_sims else 0.0
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"Error computing exemplar similarity: {e}")
        return 0.0


def _normalize_terms(items: list[str]) -> set[str]:
    terms = set()
    for item in items:
        if not item:
            continue
        tokens = re.findall(r"[a-z0-9]+", item.lower())
        terms.update(tokens)
    return terms


def _compute_explainability_score(paper_keywords: list[str], cluster_label: str | None, cluster_keywords: list[str] | None) -> float | None:
    if not paper_keywords:
        return None
    cluster_terms = _normalize_terms([cluster_label or ""])
    if cluster_keywords:
        cluster_terms |= _normalize_terms(cluster_keywords)
    if not cluster_terms:
        return None
    paper_terms = _normalize_terms(paper_keywords)
    if not paper_terms:
        return None
    intersection = paper_terms & cluster_terms
    union = paper_terms | cluster_terms
    return float(len(intersection)) / float(len(union)) if union else None


def assign_cluster(publication_id: int, title: str, abstract_text: str,
                   domain: str | None = None,
                   pdf_url: str | None = None) -> tuple[int, str, float, LLMClassificationResult, int | None, str | None, float | None]:
    """
    Assign a publication to a cluster using exemplar-based matching + domain prior.

    Steps:
        1. Build clean_text = title + abstract + PDF (first 2-3 pages)
        2. Generate embedding from clean_text
        3. Store embedding in publication_embeddings table
        4. Call Gemma LLM to get predicted categories and keywords
        5. Find nearest cluster centroid (cosine similarity >= threshold)
        6. If match: Use exemplar set for kNN second-pass verification
        7. Apply domain boost if paper domain matches cluster domain
        8. If high exemplar similarity: assign to cluster, update centroid
        9. If no match: mark as pending or unconfirmed outlier

    Args:
        publication_id: The publication's database ID.
        title: Publication title.
        abstract_text: Publication abstract text.
        domain: Optional domain name for label generation.
        pdf_url: Optional URL of the PDF for text extraction (first 2-3 pages).

    Returns:
        Tuple of (cluster_id, cluster_label, confidence, LLMClassificationResult,
        suggested_cluster_id, suggested_cluster_label).
    """
    # Combine title + abstract + extracted PDF text
    clean_text, pdf_text = _build_clean_text(title, abstract_text, pdf_url)
    embedding = get_embedding(clean_text)

    # Call LLM for keywords only (no paper-level categories)
    llm_result = generate_keywords_for_paper(title, abstract_text, pdf_text)

    # Store the embedding
    store_embedding(publication_id, embedding)

    # Try to find top-3 candidate clusters
    candidates = get_top_k_clusters(embedding, k=3)

    if candidates:
        best = None
        best_explainability = None
        best_suggested = None

        for cluster_id, cluster_label, similarity, cluster_tightness in candidates:
            dynamic_threshold = settings.SIMILARITY_THRESHOLD
            if cluster_tightness is not None:
                dynamic_threshold = max(
                    settings.MIN_ASSIGNMENT_THRESHOLD,
                    min(settings.MAX_ASSIGNMENT_THRESHOLD, cluster_tightness * settings.DYNAMIC_THRESHOLD_MULTIPLIER),
                )

            exemplars = get_cluster_exemplars(cluster_id)
            if exemplars:
                exemplar_pub_ids = [pub_id for pub_id, _ in exemplars]
                exemplar_similarity = _compute_exemplar_similarity(embedding, exemplar_pub_ids)
            else:
                exemplar_similarity = similarity

            adjusted_similarity = exemplar_similarity
            cluster_domain_info = get_cluster_domain_prior(cluster_id)
            if cluster_domain_info and domain is not None:
                cluster_domain, _ = cluster_domain_info
                if cluster_domain and cluster_domain.lower() == domain.lower():
                    adjusted_similarity += 0.05

            if best is None or adjusted_similarity > best["adjusted_similarity"]:
                label, keywords = get_cluster_label_keywords(cluster_id)
                best_explainability = _compute_explainability_score(llm_result.get("keywords", []), label, keywords)
                best = {
                    "cluster_id": cluster_id,
                    "cluster_label": cluster_label,
                    "adjusted_similarity": adjusted_similarity,
                    "dynamic_threshold": dynamic_threshold,
                }
                best_suggested = (cluster_id, cluster_label, adjusted_similarity)

        if best:
            if best["adjusted_similarity"] >= best["dynamic_threshold"]:
                update_publication_cluster(publication_id, best["cluster_id"], best["cluster_label"])
                clear_publication_pending(publication_id)
                update_cluster_centroid_running_mean(best["cluster_id"], embedding)
                return (best["cluster_id"], best["cluster_label"], best["adjusted_similarity"], llm_result, None, None, best_explainability)

            if best["adjusted_similarity"] >= settings.SOFT_SIMILARITY_THRESHOLD:
                set_publication_pending(publication_id, suggested_cluster_id=best["cluster_id"])
                label = "Pending / Unconfirmed"
                update_publication_cluster(publication_id, -1, label, best["cluster_id"], best["cluster_label"])
                return (-1, label, best["adjusted_similarity"], llm_result, best["cluster_id"], best["cluster_label"], best_explainability)

            clear_publication_pending(publication_id)
            label = "Others / Unclustered"
            update_publication_cluster(publication_id, -1, label, None, None)
            return (-1, label, best["adjusted_similarity"], llm_result, None, None, None)

    # No clusters yet: mark as pending for the next HDBSCAN run
    set_publication_pending(publication_id, suggested_cluster_id=None)
    label = "Pending / Unconfirmed"
    update_publication_cluster(publication_id, -1, label, None, None)
    return (-1, label, 0.0, llm_result, None, None, None)
