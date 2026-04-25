"""
PDF text extraction module.
Downloads a PDF from a URL and extracts text from the first 2-3 pages
to enrich the embedding input alongside the abstract and title.
"""

import io
import logging
import requests
import pdfplumber

logger = logging.getLogger(__name__)

MAX_PAGES = 3  # Extract first 2-3 pages
DOWNLOAD_TIMEOUT = 30  # seconds
MAX_PDF_SIZE = 50 * 1024 * 1024  # 50 MB limit


def extract_text_from_pdf_url(pdf_url: str) -> str:
    """
    Download a PDF from a URL and extract text from the first 2-3 pages.

    Args:
        pdf_url: The URL of the PDF file.

    Returns:
        Extracted text as a single cleaned string.
        Returns empty string if extraction fails.
    """
    try:
        logger.info(f"Downloading PDF from: {pdf_url}")
        response = requests.get(pdf_url, timeout=DOWNLOAD_TIMEOUT, stream=True)
        response.raise_for_status()

        # Check content size
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_PDF_SIZE:
            logger.warning(f"PDF too large ({content_length} bytes), skipping extraction")
            return ""

        pdf_bytes = response.content
        return extract_text_from_pdf_bytes(pdf_bytes)

    except requests.RequestException as e:
        logger.warning(f"Failed to download PDF from {pdf_url}: {e}")
        return ""
    except Exception as e:
        logger.warning(f"Unexpected error downloading PDF: {e}")
        return ""


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Extract text from the first 2-3 pages of a PDF given as bytes.

    Args:
        pdf_bytes: The raw PDF file content.

    Returns:
        Extracted text as a single cleaned string.
    """
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages_to_extract = min(MAX_PAGES, len(pdf.pages))
            extracted_parts = []

            for i in range(pages_to_extract):
                page = pdf.pages[i]
                text = page.extract_text()
                if text:
                    extracted_parts.append(text.strip())

            raw_text = "\n".join(extracted_parts)
            return _clean_text(raw_text)

    except Exception as e:
        logger.warning(f"Failed to extract text from PDF: {e}")
        return ""


def _clean_text(text: str) -> str:
    """
    Clean extracted PDF text: remove excessive whitespace, fix line breaks,
    and strip out common noise (headers, footers, page numbers).

    Args:
        text: Raw extracted text.

    Returns:
        Cleaned text string.
    """
    if not text:
        return ""

    import re

    # Collapse multiple newlines into single newline
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Collapse multiple spaces into single space
    text = re.sub(r' {2,}', ' ', text)

    # Remove common PDF artifacts like standalone page numbers
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)

    # Remove lines that are just dashes or underscores (separators)
    text = re.sub(r'^[-_=]{3,}\s*$', '', text, flags=re.MULTILINE)

    # Strip leading/trailing whitespace
    text = text.strip()

    # Truncate to reasonable length (embedding models have token limits)
    # all-MiniLM-L6-v2 handles ~256 word-pieces well, but more context
    # still helps with mean pooling. Keep ~2000 words max.
    words = text.split()
    if len(words) > 2000:
        text = " ".join(words[:2000])

    return text
