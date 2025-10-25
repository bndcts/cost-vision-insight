from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.article import Article
from app.models.cost_model import CostModel
from app.models.index import Index
from app.schemas.cost_model import CostModelCreate, CostModelRead, CostModelUpdate

router = APIRouter(prefix="/cost-models", tags=["cost-models"])


@router.get("/", response_model=list[CostModelRead])
async def list_cost_models(db: AsyncSession = Depends(get_db)) -> list[CostModel]:
    result = await db.execute(
        select(CostModel)
        .options(
            selectinload(CostModel.article),
            selectinload(CostModel.index),
        )
        .order_by(CostModel.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=CostModelRead, status_code=status.HTTP_201_CREATED)
async def create_cost_model(
    payload: CostModelCreate, db: AsyncSession = Depends(get_db)
) -> CostModel:
    # Validate referenced entities exist
    article = await db.get(Article, payload.article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    index = await db.get(Index, payload.index_id)
    if not index:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Index not found")

    existing = await db.get(CostModel, (payload.article_id, payload.index_id))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cost model already exists for this article and index",
        )

    cost_model = CostModel(**payload.model_dump())
    db.add(cost_model)
    await db.commit()
    await db.refresh(cost_model)
    await db.refresh(cost_model, attribute_names=["article", "index"])
    return cost_model


@router.patch("/{article_id}/{index_id}", response_model=CostModelRead)
async def update_cost_model(
    article_id: int,
    index_id: int,
    payload: CostModelUpdate,
    db: AsyncSession = Depends(get_db),
) -> CostModel:
    cost_model = await db.get(CostModel, (article_id, index_id))
    if not cost_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cost model not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cost_model, field, value)

    await db.commit()
    await db.refresh(cost_model)
    await db.refresh(cost_model, attribute_names=["article", "index"])
    return cost_model


@router.delete("/{article_id}/{index_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cost_model(
    article_id: int, index_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    cost_model = await db.get(CostModel, (article_id, index_id))
    if not cost_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cost model not found")

    await db.delete(cost_model)
    await db.commit()
