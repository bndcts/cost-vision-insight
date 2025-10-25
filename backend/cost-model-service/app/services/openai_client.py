from __future__ import annotations

import logging
from enum import Enum
from io import BytesIO
from typing import Any

from fastapi import HTTPException, status
from openai import OpenAI
from pydantic import BaseModel

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Get or create the OpenAI client singleton."""
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


class IndexName(str, Enum):
    """Enum of all available cost indices."""
    ALUMINIUM = "Aluminium [€/t] (Finanzen.net)"
    BLEI = "Blei [€/t] (Finanzen.net)"
    ZINK = "Zink [€/t] (Finanzen,net)"
    NICKEL = "Nickel [€/t] (Finanzen.net)"
    KUPFER = "Kupfer [€/t]"
    EISENERZ = "Eisenerz [€/t] (Finanzen.net)"
    STROM = "Strom [€/MWh] (Finanzen.net)"
    ARBEITSKOSTEN_DEUTSCHLAND = "Arbeitskosten Deutschland [€/h] (Eurostat)"
    PLATINUM = "Platinum [€/g] (Heraeus)"
    GOLD = "Gold [€/g] (Heraeus)"
    SILBER = "Silber [€/kg] (Heraeus)"
    PALLADIUM = "Palladium [€/g] (Heraeus)"
    RHODIUM = "Rhodium [€/g] (Heraeus)"
    IRIDIUM = "Iridium [€/g] (Heraeus)"
    RUTHENIUM = "Ruthenium [€/g] (Heraeus)"
    ERDGAS = "Erdgas [€/MWh] (Finanzen.net)"
    STAHL_HRB = "Stahl HRB [€/t] (SteelBenchmarker)"
    ABS_GRANULAT = "ABS Granulat [€/kg] (Plasticker)"
    PC_GRANULAT = "PC Granulat [€/kg] (Plasticker)"
    PBT_GRANULAT = "PBT Granulat [€/kg] (Plasticker)"
    PA6_GRANULAT = "PA 6 Granulat [€/kg] (Plasticker)"
    PA66_GRANULAT = "PA 6.6 Granulat [€/kg] (Plasticker)"
    POM_GRANULAT = "POM Granulat [€/kg] (Plasticker)"
    PEHD_GRANULAT = "PE-HD Granulat [€/kg] (Plasticker)"
    PELD_GRANULAT = "PE-LD [€/kg] (Plasticker)"
    PP = "PP [€/kg] (Plasticker)"
    PS = "PS [€/kg] (Plasticker)"
    HOLZ = "Holz [€/t] (finanzen.net)"
    MESSING_MS_58 = "Messing MS 58 1. V. Stufe [€/kg] (Westmetall)"
    MOLYBDAEN = "Molybdän [€/kg]"


class Unit(str, Enum):
    """Unit for weight measurements."""
    G = "g"


class MaterialIndex(BaseModel):
    """A single material/index with its quantity in grams."""
    index_name: IndexName
    quantity_grams: float
    unit: Unit = Unit.G


class ProductAnalysisResponse(BaseModel):
    """Response from OpenAI product analysis with structured data."""
    indices: list[MaterialIndex]
    total_weight_grams: float
    unit: Unit = Unit.G


def analyze_product_specification(
    file_content: bytes,
    filename: str,
    model: str | None = None,
) -> ProductAnalysisResponse:
    """
    Analyze a product specification file using OpenAI's structured output.
    
    This function:
    1. Uploads the file to OpenAI
    2. Analyzes it to extract materials and their quantities
    3. Extracts the total product weight
    4. Returns structured data with Pydantic validation
    
    Args:
        file_content: The file content as bytes
        filename: The filename (for file upload)
        model: Optional OpenAI model to use (defaults to settings.openai_model)
    
    Returns:
        ProductAnalysisResponse with indices (materials) and total weight
        
    Raises:
        HTTPException: If OpenAI API fails or returns invalid data
    """
    client = _get_client()
    
    logger.info(f"Analyzing product specification file: {filename}")
    
    try:
        # Step 1: Upload file to OpenAI
        file_like = BytesIO(file_content)
        file_like.name = filename  # Set filename for proper content type detection
        
        logger.info(f"Uploading file {filename} to OpenAI")
        uploaded_file = client.files.create(
            file=file_like,
            purpose="user_data"
        )
        logger.info(f"File uploaded successfully with ID: {uploaded_file.id}")
        
        # Step 2: Call OpenAI with structured output parsing
        logger.info("Calling OpenAI for product analysis with structured output")
        completion = client.chat.completions.parse(
            model='gpt-4o',
            response_format=ProductAnalysisResponse,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a procurement expert who analyzes product specifications "
                        "and builds should-cost models. You identify materials and quantities "
                        "with precision, always returning data in the specified format."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "file",
                            "file": {
                                "file_id": uploaded_file.id,
                            }
                        },
                        {
                            "type": "text",
                            "text": (
                                "You are building a should cost model for the product described in the attached file. "
                                "You may ONLY use the materials and indices defined in the IndexName type as allowed material cost references. "
                                "\n\n"
                                "Your tasks:\n"
                                "1. Identify the total weight of the product in grams\n"
                                "2. Analyze the product's material composition\n"
                                "3. For each material constituent, identify:\n"
                                "   - Which IndexName from the enum best matches it\n"
                                "   - The quantity of that material in grams\n"
                                "\n"
                                "Important rules:\n"
                                "- All quantities must be in grams (g)\n"
                                "- Only use index names from the IndexName enum\n"
                                "- The sum of all material quantities should equal or approximate the total weight\n"
                                "- If a material cannot be matched to an available index, exclude it\n"
                                "- Be conservative and realistic with material estimates\n"
                                "\n"
                                "Return the structured data with:\n"
                                "- indices: list of materials with their IndexName and quantity in grams\n"
                                "- total_weight_grams: total product weight in grams\n"
                                "- unit: always 'g'"
                            ),
                        },
                    ]
                }
            ],
        )
        
        if not completion.choices:
            logger.error("OpenAI returned empty response")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OpenAI API returned an empty response",
            )
        
        # Step 3: Extract and validate the parsed response
        parsed_response = completion.choices[0].message.parsed
        
        if not parsed_response:
            logger.error("OpenAI returned no parsed data")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OpenAI failed to parse response into expected format",
            )
        
        logger.info(
            f"Successfully analyzed {filename}: "
            f"total_weight={parsed_response.total_weight_grams}g, "
            f"materials={len(parsed_response.indices)}"
        )
        
        # Log the materials found
        for idx, material in enumerate(parsed_response.indices, 1):
            logger.info(
                f"  Material {idx}: {material.index_name.value} = {material.quantity_grams}g"
            )
        
        return parsed_response
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error analyzing product specification: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to analyze product specification: {str(exc)}",
        )


def estimate_costs(prompt: str, model: str | None = None) -> dict[str, Any]:
    """
    Legacy function for cost estimation.
    Kept for backward compatibility with existing endpoints.
    """
    client = _get_client()
    response = client.chat.completions.create(
        model=model or settings.openai_model,
        messages=[
            {"role": "system", "content": "You are a cost modeling assistant."},
            {"role": "user", "content": prompt},
        ],
    )

    if not response.choices:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenAI API returned an empty response",
        )

    message = response.choices[0].message
    return {"raw": message.content}
