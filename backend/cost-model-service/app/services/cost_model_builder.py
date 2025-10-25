from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.index import Index


ALIAS_TO_INDEX_NAME: dict[str, str] = {
    "steel": "Stahl HRB [€/t] (SteelBenchmarker)",
    "stainless steel": "Stahl HRB [€/t] (SteelBenchmarker)",
    "carbon steel": "Stahl HRB [€/t] (SteelBenchmarker)",
    "aluminum": "Aluminium [€/t] (Finanzen.net)",
    "aluminium": "Aluminium [€/t] (Finanzen.net)",
    "nickel": "Nickel [€/t] (Finanzen.net)",
    "copper": "Kupfer [€/t]",
    "zinc": "Zink [€/t] (Finanzen,net)",
    "lead": "Blei [€/t] (Finanzen.net)",
    "iron": "Eisenerz [€/t] (Finanzen.net)",
    "iron ore": "Eisenerz [€/t] (Finanzen.net)",
    "abs": "ABS Granulat [€/kg] (Plasticker)",
    "abs plastic": "ABS Granulat [€/kg] (Plasticker)",
    "polycarbonate": "PC Granulat [€/kg] (Plasticker)",
    "pc": "PC Granulat [€/kg] (Plasticker)",
    "pbt": "PBT Granulat [€/kg] (Plasticker)",
    "pa6": "PA 6 Granulat [€/kg] (Plasticker)",
    "pa 6": "PA 6 Granulat [€/kg] (Plasticker)",
    "pa66": "PA 6.6 Granulat [€/kg] (Plasticker)",
    "pa 6.6": "PA 6.6 Granulat [€/kg] (Plasticker)",
    "pom": "POM Granulat [€/kg] (Plasticker)",
    "pehd": "PE-HD Granulat [€/kg] (Plasticker)",
    "pe hd": "PE-HD Granulat [€/kg] (Plasticker)",
    "peld": "PE-LD [€/kg] (Plasticker)",
    "pe ld": "PE-LD [€/kg] (Plasticker)",
    "pp": "PP [€/kg] (Plasticker)",
    "ps": "PS [€/kg] (Plasticker)",
    "wood": "Holz [€/t] (finanzen.net)",
    "brass": "Messing MS 58 1. V. Stufe [€/kg] (Westmetall)",
    "gold": "Gold [€/g] (Heraeus)",
    "silver": "Silber [€/kg] (Heraeus)",
    "platinum": "Platinum [€/g] (Heraeus)",
    "palladium": "Palladium [€/g] (Heraeus)",
    "rhodium": "Rhodium [€/g] (Heraeus)",
    "iridium": "Iridium [€/g] (Heraeus)",
    "ruthenium": "Ruthenium [€/g] (Heraeus)",
}


@dataclass(slots=True)
class CostModelPart:
    index_id: int
    fraction: float  # normalized share (0-1) of total mass


def _normalize(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


async def _latest_indices_by_name(db: AsyncSession) -> dict[str, Index]:
    stmt = select(Index).order_by(Index.name.asc(), Index.date.desc())
    result = await db.execute(stmt)
    indices: dict[str, Index] = {}
    for row in result.scalars():
        if row.name not in indices:
            indices[row.name] = row
    return indices


def _match_index(material_name: str, indices_by_name: dict[str, Index]) -> Index | None:
    normalized = _normalize(material_name)
    for alias, index_name in ALIAS_TO_INDEX_NAME.items():
        if alias in normalized:
            index = indices_by_name.get(index_name)
            if index and index.value_per_gram is not None:
                return index
    # direct lookup by canonical name if OpenAI already returned it
    direct = indices_by_name.get(material_name)
    if direct and direct.value_per_gram is not None:
        return direct
    return None


async def build_cost_model_parts(
    materials: list[dict[str, Any]],
    db: AsyncSession,
) -> list[CostModelPart]:
    """
    Convert extracted material percentages into CostModelPart entries
    normalized to sum to 1.0.
    """
    if not materials:
        return []

    indices_by_name = await _latest_indices_by_name(db)
    raw_parts: list[CostModelPart] = []

    for material_entry in materials:
        material = (material_entry or {}).get("material")
        percentage = (material_entry or {}).get("percentage")
        if not material or percentage is None:
            continue
        try:
            pct_value = float(percentage)
        except (TypeError, ValueError):
            continue
        if pct_value <= 0:
            continue

        index = _match_index(material, indices_by_name)
        if not index:
            continue

        clamped_pct = min(max(pct_value, 0.0), 1.0)
        raw_parts.append(CostModelPart(index_id=index.id, fraction=clamped_pct))

    if not raw_parts:
        return []

    total = sum(part.fraction for part in raw_parts)
    if total <= 0:
        return []

    normalized_parts = [
        CostModelPart(
            index_id=part.index_id,
            fraction=round(part.fraction / total, 6),
        )
        for part in raw_parts
    ]

    return normalized_parts
