from __future__ import annotations

import logging
from enum import Enum
from io import BytesIO

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
    labor_hours: float | None = None
    electricity_kwh: float | None = None


def analyze_product_specification(
    file_content: bytes,
    filename: str,
    similar_products_context: str | None = None,
    model: str | None = None,
    article_price_eur: float | None = None,
    article_context: str | None = None,
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
        similar_products_context: Optional context from similar products' cost models
        model: Optional OpenAI model to use (defaults to settings.openai_model)
        article_price_eur: Optional known market/order price for one unit (EUR)
        article_context: Optional textual context/complexity description for the article
    
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

        context_lines: list[str] = []
        if article_price_eur is not None:
            context_lines.append(
                f"Observed market price ≈ {article_price_eur:.2f} EUR per unit. "
                "Ensure the combined materials, labor, and electricity align with this reality."
            )
        if article_context:
            context_lines.append(f"Article context/complexity: {article_context.strip()}")

        extra_context = ""
        if context_lines:
            extra_context = "\n5. Additional context:\n" + "\n".join(
                f"   - {line}" for line in context_lines
            )
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
                                + (f"SIMILAR PRODUCTS REFERENCE:\n{similar_products_context}\n\n" if similar_products_context else "")
                                + "Your tasks:\n"
                                "1. Identify the total weight of the product in grams\n"
                                "2. Analyze the product's material composition\n"
                                "3. For each material constituent, identify:\n"
                                "   - Which IndexName from the enum best matches it\n"
                                "   - The quantity of that material in grams\n"
                                "4. Estimate the manufacturing effort required strictly for ONE unit of the product:\n"
                                "   - Total labor hours (in hours) spent on producing a single unit from start to finish\n"
                                "   - Total electricity consumption (in kWh) for that same single unit\n"
                                f"{extra_context}\n"
                                "\n"
                                "Important rules:\n"
                                "- All quantities must be in grams (g)\n"
                                "- Only use index names from the IndexName enum\n"
                                "- The sum of all material quantities should equal or approximate the total weight\n"
                                "- If a material cannot be matched to an available index, exclude it\n"
                                "- Be conservative and realistic with material estimates\n"
                                + ("- Use the similar products above as reference for material composition and quantities\n" if similar_products_context else "")
                                + "\n"
                                "- Labor and electricity must represent ONLY the effort/energy to build a single unit, "
                                "but electricity should include the incremental machine usage, workstation lighting, and other direct production overhead for that part."
                                "\n"
                                "Return the structured data with:\n"
                                "- indices: list of materials with their IndexName and quantity in grams\n"
                                "- total_weight_grams: total product weight in grams\n"
                                "- unit: always 'g'\n"
                                "- labor_hours: total labor hours consumed per unit (float)\n"
                                "- electricity_kwh: total electricity consumption per unit (float)\n"
                                "\n"
                                "Calibration guidance:\n"
                                "- For small fittings or machined components, direct labor should rarely exceed a few minutes. Unless drawings clearly indicate long manual processing, keep labor estimates between 0.03 h and 0.25 h (≈2-15 minutes) per unit.\n"
                                "- Electricity usage per unit is typically modest (fractions of a single kWh up to ~5 kWh). Only exceed this if the spec explicitly describes very energy-intensive processing."
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
