from __future__ import annotations

import json
import logging
import io
from typing import Any

from fastapi import HTTPException, status
from openai import OpenAI

from app.core.config import get_settings

# Optional PDF text extraction (avoid hard crash if not installed at runtime)
try:
    from pypdf import PdfReader  # type: ignore
except Exception:  # pragma: no cover - best-effort import
    PdfReader = None  # type: ignore

settings = get_settings()
logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is not None:
        return _client
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI API key not configured",
        )
    _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def extract_metadata_from_file(
    file_content: bytes, 
    filename: str,
    model: str | None = None
) -> dict[str, Any]:
    """
    Extract product weight from a specification file using OpenAI.
    
    Args:
        file_content: The file content as bytes
        filename: The filename (for logging)
        model: Optional OpenAI model to use
    
    Returns:
        Dictionary with 'unit_weight_grams' key (float or None)
        Example: {"unit_weight_grams": 2500.0}
    """
    client = _get_client()

    # If PDF, extract text locally (first pages) and proceed with text-based extraction
    if filename.lower().endswith(".pdf"):
        text_content = ""
        try:
            if PdfReader is None:
                logger.warning("pypdf not installed; cannot parse PDF. Returning no weight.")
                return {"unit_weight_grams": None}

            reader = PdfReader(io.BytesIO(file_content))  # type: ignore[misc]
            # Extract from first up to 10 pages to stay efficient
            for page_index, page in enumerate(reader.pages[:10]):  # type: ignore[index]
                try:
                    text_content += page.extract_text() or ""
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {filename}: {e}")
            return {"unit_weight_grams": None}

        # Limit content size
        text_content = text_content[:8000]

        prompt = f"""Extract the product weight in grams from the following product specification document.

Document filename: {filename}

Content:
{text_content}

Instructions:
- Find the product weight/mass in the document
- Convert it to grams (g) if it's in a different unit (kg, mg, lb, oz, etc.)
- Return ONLY a JSON object with this exact format:
{{"unit_weight_grams": <weight as number in grams, or null if not found>}}

Examples:
- If weight is "2.5 kg", return: {{"unit_weight_grams": 2500}}
- If weight is "500 g", return: {{"unit_weight_grams": 500}}
- If weight is "1.2 lb", return: {{"unit_weight_grams": 544.31}}
- If no weight found, return: {{"unit_weight_grams": null}}

Return ONLY the JSON object, no explanations or additional text."""

        try:
            logger.info(f"Calling OpenAI to extract weight from PDF {filename} (text mode)")
            chat_response = client.chat.completions.create(
                model=model or settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise data extraction assistant. You extract product weight from specifications and return valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            if not chat_response.choices:
                logger.error("OpenAI returned empty response")
                return {"unit_weight_grams": None}

            message_content = chat_response.choices[0].message.content
            if not message_content:
                logger.error("OpenAI returned empty message content")
                return {"unit_weight_grams": None}

            logger.info(f"OpenAI response: {message_content}")

            try:
                cleaned_content = message_content.strip()
                if cleaned_content.startswith("```"):
                    parts = cleaned_content.split("```")
                    if len(parts) >= 2:
                        cleaned_content = parts[1]
                        if cleaned_content.startswith("json"):
                            cleaned_content = cleaned_content[4:]
                        cleaned_content = cleaned_content.strip()

                result = json.loads(cleaned_content)

                if "unit_weight_grams" not in result:
                    logger.error(f"Response missing 'unit_weight_grams' key: {result}")
                    return {"unit_weight_grams": None}

                weight = result["unit_weight_grams"]
                if weight is not None:
                    logger.info(f"Successfully extracted weight: {weight}g from {filename}")
                else:
                    logger.info(f"No weight found in {filename}")

                return result

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI response as JSON: {e}")
                logger.error(f"Response was: {message_content}")
                return {"unit_weight_grams": None}

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
            return {"unit_weight_grams": None}

    # Fallback for non-PDFs: try text-based extraction
    client = _get_client()

    try:
        # Decode file content (text-based files)
        try:
            text_content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            logger.warning(f"Could not decode file {filename} as UTF-8, trying latin-1")
            try:
                text_content = file_content.decode('latin-1')
            except Exception as e:
                logger.error(f"Failed to decode file {filename}: {e}")
                return {"unit_weight_grams": None}

        text_content = text_content[:8000]

        prompt = f"""Extract the product weight in grams from the following product specification document.

Document filename: {filename}

Content:
{text_content}

Instructions:
- Find the product weight/mass in the document
- Convert it to grams (g) if it's in a different unit (kg, mg, lb, oz, etc.)
- Return ONLY a JSON object with this exact format:
{{"unit_weight_grams": <weight as number in grams, or null if not found>}}

Examples:
- If weight is "2.5 kg", return: {{"unit_weight_grams": 2500}}
- If weight is "500 g", return: {{"unit_weight_grams": 500}}
- If weight is "1.2 lb", return: {{"unit_weight_grams": 544.31}}
- If no weight found, return: {{"unit_weight_grams": null}}

Return ONLY the JSON object, no explanations or additional text."""

        logger.info(f"Calling OpenAI to extract weight from {filename} (text mode)")

        chat_response = client.chat.completions.create(
            model=model or settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise data extraction assistant. You extract product weight from specifications and return valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=100,
        )

        if not chat_response.choices:
            logger.error("OpenAI returned empty response")
            return {"unit_weight_grams": None}

        message_content = chat_response.choices[0].message.content
        if not message_content:
            logger.error("OpenAI returned empty message content")
            return {"unit_weight_grams": None}

        logger.info(f"OpenAI response: {message_content}")

        try:
            cleaned_content = message_content.strip()
            if cleaned_content.startswith("```"):
                parts = cleaned_content.split("```")
                if len(parts) >= 2:
                    cleaned_content = parts[1]
                    if cleaned_content.startswith("json"):
                        cleaned_content = cleaned_content[4:]
                    cleaned_content = cleaned_content.strip()

            result = json.loads(cleaned_content)

            if "unit_weight_grams" not in result:
                logger.error(f"Response missing 'unit_weight_grams' key: {result}")
                return {"unit_weight_grams": None}

            weight = result["unit_weight_grams"]
            if weight is not None:
                logger.info(f"Successfully extracted weight: {weight}g from {filename}")
            else:
                logger.info(f"No weight found in {filename}")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            logger.error(f"Response was: {message_content}")
            return {"unit_weight_grams": None}

    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
        return {"unit_weight_grams": None}


def generate_cost_models(
    article_name: str,
    article_description: str | None,
    unit_weight: float | None,
    available_indices: list[dict[str, Any]],
    model: str | None = None
) -> list[dict[str, Any]]:
    """
    Generate cost models for an article using OpenAI.
    
    Args:
        article_name: Name of the article
        article_description: Optional description
        unit_weight: Weight of the article in kg
        available_indices: List of available cost indices with id, name, and value
        
    Returns:
        List of cost models with structure: [{"index_id": int, "part": float}, ...]
    """
    client = _get_client()
    
    indices_str = "\n".join([
        f"- ID: {idx['id']}, Name: {idx['name']}, Current Value: {idx['value']}"
        for idx in available_indices
    ])
    
    prompt = f"""
    Generate cost models for the following article by determining what percentage (part) 
    each cost index contributes to the total cost.
    
    Article: {article_name}
    Description: {article_description or "N/A"}
    Unit Weight: {unit_weight or "N/A"} kg
    
    Available Cost Indices:
    {indices_str}
    
    Based on typical manufacturing cost structures, determine what percentage each index 
    contributes to the total cost. The parts should sum to 1.0 (100%).
    
    Return ONLY a valid JSON array with this structure:
    [
        {{"index_id": <id>, "part": <decimal between 0 and 1>}},
        ...
    ]
    
    Only include indices that are relevant for this product. Return ONLY the JSON array, 
    no additional text or explanation.
    """
    
    try:
        response = client.chat.completions.create(
            model=model or settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a cost modeling expert. You analyze products and determine cost structure breakdowns."},
                {"role": "user", "content": prompt},
            ],
        )

        if not response.choices:
            logger.error("OpenAI returned empty response for cost model generation")
            return []

        message_content = response.choices[0].message.content
        
        if not message_content:
            logger.error("OpenAI returned empty message content")
            return []
        
        # Try to parse JSON response
        try:
            # Remove markdown code blocks if present
            if message_content.strip().startswith("```"):
                message_content = message_content.strip()
                message_content = message_content.split("```")[1]
                if message_content.startswith("json"):
                    message_content = message_content[4:]
                message_content = message_content.strip()
            
            cost_models = json.loads(message_content)
            logger.info(f"Successfully generated {len(cost_models)} cost models")
            return cost_models
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            logger.error(f"Response was: {message_content}")
            return []
            
    except Exception as e:
        logger.error(f"Error calling OpenAI for cost model generation: {e}")
        raise


def estimate_costs(prompt: str, model: str | None = None) -> dict[str, Any]:
    """Legacy function for cost estimation"""
    client = _get_client()
    response = client.chat.completions.create(
        model=model or settings.openai_model,
        messages=[
            {"role": "system", "content": "You are a cost modeling assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    if not response.choices:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenAI API returned an empty response",
        )

    message = response.choices[0].message
    return {"raw": message.content}
