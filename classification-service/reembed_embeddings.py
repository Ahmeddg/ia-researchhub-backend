"""
Re-embed all existing publications and rebuild clusters using the current model.

Environment variables:
  REEMBED_BATCH_SIZE=64
  REEMBED_USE_PDF=0              # 1 to include PDF text in embeddings
  REEMBED_MAX_PDF_CHARS=8000     # trim PDF text for embedding
  REEMBED_RESET_CLUSTERS=1       # 1 to reset clusters before recluster
"""

from __future__ import annotations

import os
import psycopg2
from app.config import settings
from app.db import get_connection, register_vector_safely, reset_clusters
from app.embedding import get_embeddings_batch
from app.pdf_extractor import extract_text_from_pdf_url
from app.recluster import recluster_all


def _build_text(title: str | None, abstract_text: str | None, pdf_url: str | None, use_pdf: bool, max_pdf_chars: int) -> str:
    parts = []
    if title:
        parts.append(title)
    if abstract_text:
        parts.append(abstract_text)
    if use_pdf and pdf_url:
        pdf_text = extract_text_from_pdf_url(pdf_url)
        if pdf_text:
            parts.append(pdf_text[:max_pdf_chars])
    return ". ".join(parts)


def reembed_all() -> None:
    batch_size = int(os.getenv("REEMBED_BATCH_SIZE", "64"))
    use_pdf = os.getenv("REEMBED_USE_PDF", "0") == "1"
    max_pdf_chars = int(os.getenv("REEMBED_MAX_PDF_CHARS", "8000"))
    reset = os.getenv("REEMBED_RESET_CLUSTERS", "1") == "1"

    print(f"Re-embedding with model: {settings.MODEL_NAME}")
    print(f"Batch size: {batch_size}, Use PDF: {use_pdf}, Reset clusters: {reset}")

    last_id = 0
    total_processed = 0

    while True:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                try:
                    cur.execute("""
                        SELECT id, title, abstract_text, pdf_url
                        FROM publications
                        WHERE id > %s
                        ORDER BY id
                        LIMIT %s;
                    """, (last_id, batch_size))
                except psycopg2.errors.UndefinedColumn:
                    conn.rollback()
                    cur.execute("""
                        SELECT id, title, abstract_text, NULL
                        FROM publications
                        WHERE id > %s
                        ORDER BY id
                        LIMIT %s;
                    """, (last_id, batch_size))
                rows = cur.fetchall()
        finally:
            conn.close()

        if not rows:
            break

        pub_ids: list[int] = []
        texts: list[str] = []
        for pub_id, title, abstract_text, pdf_url in rows:
            pub_ids.append(int(pub_id))
            texts.append(_build_text(title, abstract_text, pdf_url, use_pdf, max_pdf_chars))

        embeddings = get_embeddings_batch(texts)

        conn = get_connection()
        register_vector_safely(conn)
        try:
            with conn.cursor() as cur:
                cur.executemany("""
                    INSERT INTO publication_embeddings (publication_id, embedding)
                    VALUES (%s, %s::vector)
                    ON CONFLICT (publication_id)
                    DO UPDATE SET embedding = EXCLUDED.embedding;
                """, [(pid, emb) for pid, emb in zip(pub_ids, embeddings)])
                conn.commit()
        finally:
            conn.close()

        last_id = pub_ids[-1]
        total_processed += len(pub_ids)
        print(f"Processed {total_processed} publications...")

    if reset:
        print("Resetting clusters before recluster...")
        reset_clusters()

    print("Rebuilding clusters...")
    summary = recluster_all()
    print(f"Re-embed complete. Summary: {summary}")


if __name__ == "__main__":
    reembed_all()
    # summary = recluster_all()
    # print(f"Re-embed complete. Summary: {summary}")