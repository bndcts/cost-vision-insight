from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.article import Article
from app.models.cost_model import CostModel
from app.schemas.estimates import CostEstimateRequest, CostEstimateResponse
from app.services.openai_client import estimate_costs

router = APIRouter(prefix="/cost-estimates", tags=["estimates"])


@router.post("/", response_model=CostEstimateResponse)
async def generate_cost_estimate(
    payload: CostEstimateRequest, db: AsyncSession = Depends(get_db)
) -> CostEstimateResponse:
    result = await db.execute(
        select(Article)
        .options(
            selectinload(Article.cost_models).selectinload(CostModel.index),
        )
        .where(Article.id == payload.article_id)
    )
    article = result.scalars().first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    lines = [
        f"Article: {article.article_name}",
        f"Description: {article.description or 'n/a'}",
    ]

    if article.unit_weight is not None:
        lines.append(f"Unit weight: {article.unit_weight}")

    if article.cost_models:
        lines.append("Cost model contributions:")
        for cm in article.cost_models:
            if cm.index:
                lines.append(
                    f"- {cm.index.name} ({cm.index.unit}) factor {cm.index.price_factor} share {cm.part}"
                )
            else:
                lines.append(f"- Index ID {cm.index_id} share {cm.part}")
    else:
        lines.append("No index contributions linked yet.")

    if payload.context:
        lines.append(f"Additional context: {payload.context}")

    prompt = "\n".join(lines)

    try:
        openai_response = estimate_costs(prompt)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to query OpenAI: {exc}",
        ) from exc

    return CostEstimateResponse(
        article_id=article.id,
        prompt=prompt,
        raw_response=openai_response.get("raw"),
    )
