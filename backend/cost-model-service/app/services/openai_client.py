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
    labor_cost_eur: float | None = None
    electricity_cost_eur: float | None = None
    other_manufacturing_costs_eur: float | None = None


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
                                "You are building a complete should-cost model for the product described in the attached file. "
                                "You will estimate ALL costs directly in EUR, except for raw materials which must use the predefined IndexName types. "
                                "\n\n"
                                + (f"SIMILAR PRODUCTS REFERENCE:\n{similar_products_context}\n\n" if similar_products_context else "")
                                + "Your tasks:\n"
                                "1. Identify the total weight of the product in grams\n"
                                "2. Analyze the product's material composition:\n"
                                "   - For each material constituent, identify which IndexName from the enum best matches it\n"
                                "   - Specify the quantity of that material in grams\n"
                                "   - Only use index names from the IndexName enum for materials\n"
                                "3. Estimate ALL manufacturing costs directly in EUR for ONE unit:\n"
                                "   - labor_cost_eur: Direct labor cost in EUR for producing one unit (consider wages, skill level, time)\n"
                                "   - electricity_cost_eur: Electricity cost in EUR for producing one unit (machinery, lighting, equipment)\n"
                                "   - other_manufacturing_costs_eur: All other manufacturing costs in EUR per unit (tooling, depreciation, setup, quality control, packaging, etc.)\n"
                                f"{extra_context}\n"
                                "\n"
                                "Important rules:\n"
                                "- Material quantities must be in grams (g)\n"
                                "- Only use index names from the IndexName enum for materials\n"
                                "- The sum of all material quantities should equal or approximate the total weight\n"
                                "- If a material cannot be matched to an available index, exclude it\n"
                                "- Be conservative and realistic with all estimates\n"
                                + ("- Use the similar products above as reference for material composition and cost estimates\n" if similar_products_context else "")
                                + "\n"
                                "Cost estimation guidance:\n"
                                "- Consider typical European manufacturing labor rates (€20-50/hour depending on skill)\n"
                                "- Consider typical industrial electricity rates (€0.15-0.30/kWh)\n"
                                "- For small machined parts: labor is typically €0.50-5.00, electricity €0.10-1.00\n"
                                "- For larger assemblies: labor can be €5-50, electricity €1-10\n"
                                "- Other manufacturing costs typically add 20-40% on top of direct labor and material\n"
                                "- The TOTAL cost (materials + labor + electricity + other) should reasonably align with the market price if provided\n"
                                "- If market price is low, all non-material costs must be correspondingly low\n"
                                "\n"
                                "Return the structured data with:\n"
                                "- indices: list of materials with their IndexName and quantity in grams\n"
                                "- total_weight_grams: total product weight in grams\n"
                                "- unit: always 'g'\n"
                                "- labor_cost_eur: direct labor cost in EUR per unit\n"
                                "- electricity_cost_eur: electricity cost in EUR per unit\n"
                                "- other_manufacturing_costs_eur: all other manufacturing costs in EUR per unit"
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
            f"materials={len(parsed_response.indices)}, "
            f"labor_cost={parsed_response.labor_cost_eur}€, "
            f"electricity_cost={parsed_response.electricity_cost_eur}€, "
            f"other_costs={parsed_response.other_manufacturing_costs_eur}€"
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
