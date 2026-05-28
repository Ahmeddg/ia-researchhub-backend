"""
LLM Integration module using Ollama Cloud (Gemma 3).
Connects to the Ollama Cloud API to automatically categorize and extract keywords
for publications based on their title, abstract, and PDF contents.
"""

import json
import logging
import requests
from typing import TypedDict
from app.config import settings

logger = logging.getLogger(__name__)


class CategoryPrediction(TypedDict):
    category: str
    confidence: float
    reason: str


class LLMClassificationResult(TypedDict):
    title: str
    predicted_categories: list[CategoryPrediction]
    keywords: list[str]


class LLMClusterLabelResult(TypedDict):
    name: str
    description: str
    keywords: list[str]


def generate_categories_and_keywords(title: str, abstract_text: str, pdf_text: str = "") -> LLMClassificationResult:
    """
    Call Ollama API (Gemma 3) to generate predicted categories and keywords.
    
    Args:
        title: Publication title.
        abstract_text: Publication abstract.
        pdf_text: Extracted PDF text.
        
    Returns:
        LLMClassificationResult containing predicted_categories and keywords.
    """
    prompt = f"""
You are an expert scientific publication classifier.

Your task is to analyze the following scientific publication and automatically determine the most relevant scientific categories/domains.

### INPUT DATA
Title:
{title}

Abstract:
{abstract_text}

Extracted PDF Content:
{pdf_text[:4000]}

### TASK
1. Determine the most relevant scientific categories (domains).
2. Provide the top 5 categories (most relevant first).
3. Provide a confidence score between 0 and 1.
4. Provide a short justification for each category.
5. Also generate 5 keywords describing the paper.

### OUTPUT FORMAT
Return ONLY valid JSON in the following format:

{{
  "title": "{title}",
  "predicted_categories": [
    {{
      "category": "...",
      "confidence": 0.0,
      "reason": "..."
    }}
  ],
  "keywords": ["...", "...", "...", "...", "..."]
}}
"""

    payload = {
        "model": settings.OLLAMA_MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    headers = {
        "Authorization": f"Bearer {settings.OLLAMA_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        logger.info(f"Calling Ollama API ({settings.OLLAMA_MODEL_NAME}) for publication: '{title}'")
        response = requests.post(settings.OLLAMA_API_URL, json=payload, headers=headers, timeout=60)
        
        if response.status_code != 200:
            logger.error(f"Ollama API Error ({response.status_code}): {response.text}")
            return _fallback_result(title)
            
        response_text = _extract_json_from_response(response.json().get("response", ""))
        parsed_result = json.loads(response_text)
        
        return {
            "title": title,
            "predicted_categories": parsed_result.get("predicted_categories", []),
            "keywords": parsed_result.get("keywords", [])
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Ollama response: {e}\nResponse: {response_text}")
        return _fallback_result(title)
    except Exception as e:
        logger.error(f"Error calling Ollama API: {e}")
        return _fallback_result(title)


def generate_keywords_for_paper(title: str, abstract_text: str, pdf_text: str = "") -> LLMClassificationResult:
    """
    Call Ollama API (Gemma 3) to generate keywords only (no categories).

    Args:
        title: Publication title.
        abstract_text: Publication abstract.
        pdf_text: Extracted PDF text.

    Returns:
        LLMClassificationResult with empty predicted_categories and keywords populated.
    """
    prompt = f"""
You are an expert scientific publication classifier.

Your task is to extract 5 concise, specific keywords that best describe the paper.

### INPUT DATA
Title:
{title}

Abstract:
{abstract_text}

Extracted PDF Content:
{pdf_text[:4000]}

### OUTPUT FORMAT
Return ONLY valid JSON in the following format:

{{
  "keywords": ["...", "...", "...", "...", "..."]
}}
"""

    payload = {
        "model": settings.OLLAMA_MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    headers = {
        "Authorization": f"Bearer {settings.OLLAMA_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        logger.info(f"Calling Ollama API ({settings.OLLAMA_MODEL_NAME}) for paper keywords: '{title}'")
        response = requests.post(settings.OLLAMA_API_URL, json=payload, headers=headers, timeout=60)

        if response.status_code != 200:
            logger.error(f"Ollama API Error ({response.status_code}): {response.text}")
            return {"title": title, "predicted_categories": [], "keywords": []}

        response_text = _extract_json_from_response(response.json().get("response", ""))
        parsed_result = json.loads(response_text)
        return {
            "title": title,
            "predicted_categories": [],
            "keywords": parsed_result.get("keywords", []),
        }
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Ollama response: {e}\nResponse: {response_text}")
        return {"title": title, "predicted_categories": [], "keywords": []}
    except Exception as e:
        logger.error(f"Error calling Ollama API: {e}")
        return {"title": title, "predicted_categories": [], "keywords": []}


def generate_cluster_label(texts: list[str], l1_label: str | None = None, l2_label: str | None = None) -> LLMClusterLabelResult:
    """
    Call Ollama API (Gemma 3) to generate a cluster name, description, and keywords.

    Args:
        texts: List of "Title. Abstract" strings for representative papers.
        l1_label: Optional L1 category label for context.
        l2_label: Optional L2 category label for context.

    Returns:
        LLMClusterLabelResult with name, description, keywords.
    """
    context_lines = []
    if l1_label:
        context_lines.append(f"L1 field: {l1_label}")
    if l2_label:
        context_lines.append(f"L2 subfield: {l2_label}")
    context = "\n".join(context_lines)

    samples = "\n\n".join([f"- {text}" for text in texts])
    prompt = f"""
You are an expert scientific taxonomy curator.

{context}

The following papers form a coherent research cluster. Provide:
1) A concise cluster name (max 5 words, specific not generic)
2) A 2-3 sentence description of the research area
3) 5 keywords that uniquely identify this cluster

Return ONLY valid JSON in this format:
{{
  "name": "...",
  "description": "...",
  "keywords": ["...", "...", "...", "...", "..."]
}}

Papers:
{samples}
"""

    payload = {
        "model": settings.OLLAMA_MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    headers = {
        "Authorization": f"Bearer {settings.OLLAMA_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        logger.info(f"Calling Ollama API ({settings.OLLAMA_MODEL_NAME}) for cluster labeling")
        response = requests.post(settings.OLLAMA_API_URL, json=payload, headers=headers, timeout=60)

        if response.status_code != 200:
            logger.error(f"Ollama API Error ({response.status_code}): {response.text}")
            return _fallback_cluster_label()

        response_text = _extract_json_from_response(response.json().get("response", ""))
        parsed_result = json.loads(response_text)
        return {
            "name": parsed_result.get("name", "Uncategorized"),
            "description": parsed_result.get("description", ""),
            "keywords": parsed_result.get("keywords", []),
        }
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Ollama response: {e}")
        return _fallback_cluster_label()
    except Exception as e:
        logger.error(f"Error calling Ollama API: {e}")
        return _fallback_cluster_label()


def generate_taxonomy_label(items: list[str], level: str, parent_label: str | None = None) -> str | None:
    """
    Generate a semantic taxonomy label for L1/L2 groups from cluster labels.

    Args:
        items: List of cluster labels/keywords for the group.
        level: "L1" or "L2".
        parent_label: Optional parent L1 label for L2 context.

    Returns:
        A concise taxonomy label or None if parsing fails.
    """
    if not items:
        return None

    scope = "broad scientific field" if level == "L1" else "subfield"
    parent_line = f"Parent field: {parent_label}\n" if parent_label else ""
    samples = "\n".join([f"- {item}" for item in items[:15]])
    prompt = f"""
You are a scientific taxonomy curator.

{parent_line}
Given the following cluster labels/keywords, propose a concise {scope} name (max 4 words).

Return ONLY valid JSON in this format:
{{
  "label": "..."
}}

Clusters:
{samples}
"""

    payload = {
        "model": settings.OLLAMA_MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    headers = {
        "Authorization": f"Bearer {settings.OLLAMA_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        logger.info(f"Calling Ollama API ({settings.OLLAMA_MODEL_NAME}) for taxonomy label {level}")
        response = requests.post(settings.OLLAMA_API_URL, json=payload, headers=headers, timeout=60)
        if response.status_code != 200:
            logger.error(f"Ollama API Error ({response.status_code}): {response.text}")
            return None
        response_text = _extract_json_from_response(response.json().get("response", ""))
        parsed_result = json.loads(response_text)
        label = parsed_result.get("label")
        return label if isinstance(label, str) and label.strip() else None
    except Exception as e:
        logger.error(f"Error calling Ollama API for taxonomy label: {e}")
        return None


def _extract_json_from_response(response_text: str) -> str:
    # Defensive parsing in case the LLM wraps the JSON in markdown blocks
    if "```json" in response_text:
        return response_text.split("```json")[1].split("```")[0].strip()
    if "```" in response_text:
        return response_text.split("```")[1].split("```")[0].strip()
    return response_text


def _fallback_cluster_label() -> LLMClusterLabelResult:
    return {
        "name": "Uncategorized",
        "description": "",
        "keywords": []
    }

def _fallback_result(title: str) -> LLMClassificationResult:
    """Return an empty/fallback result when the LLM fails."""
    return {
        "title": title,
        "predicted_categories": [{"category": "Uncategorized AI Failure", "confidence": 0.0, "reason": "LLM API failed"}],
        "keywords": []
    }
