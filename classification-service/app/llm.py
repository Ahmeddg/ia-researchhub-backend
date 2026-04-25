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
            
        result = response.json()
        response_text = result.get("response", "")
        
        # Defensive parsing in case the LLM wraps the JSON in markdown blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
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

def _fallback_result(title: str) -> LLMClassificationResult:
    """Return an empty/fallback result when the LLM fails."""
    return {
        "title": title,
        "predicted_categories": [{"category": "Uncategorized AI Failure", "confidence": 0.0, "reason": "LLM API failed"}],
        "keywords": []
    }
