from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.article import Article
from app.models.cost_model import CostModel
from app.models.index import Index
from app.models.order import Order
from app.schemas.article import ArticleCreate, ArticleRead, ArticleUpdate

LABOR_INDEX_NAME = "Arbeitskosten Deutschland [€/h] (Eurostat)"
ELECTRICITY_INDEX_NAME = "Strom [€/MWh] (Finanzen.net)"
MASS_UNITS = {
    "g",
    "gram",
    "grams",
    "kg",
    "kilogram",
    "kilograms",
    "t",
    "ton",
    "tons",
    "tonne",
    "tonnes",
}


def _is_material_unit(unit: str | None) -> bool:
    if not unit:
        return False
    return unit.lower() in MASS_UNITS


async def _latest_article_price(article: Article, db: AsyncSession) -> float | None:
    stmt = (
        select(Order.price)
        .where(
            or_(
                Order.article_id == article.id,
                Order.article_name == article.article_name,
            )
        )
        .order_by(Order.order_date.desc())
    )
    result = await db.execute(stmt)
    price_value = result.scalars().first()
    return float(price_value) if price_value is not None else None

router = APIRouter(prefix="/articles", tags=["articles"])


class ArticleStatusResponse(BaseModel):
    """Lightweight response for polling article processing status"""
    id: int
    processing_status: str
    processing_error: Optional[str] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None


class IndexValuePoint(BaseModel):
    """A single data point for an index value at a specific date"""
    date: date
    value: float
    unit_value: Optional[float] = None


class ArticleIndexData(BaseModel):
    """Time series data for a single index used in an article"""
    index_id: int
    index_name: str
    unit: str
    quantity_value: float
    quantity_unit: str
    is_material: bool = False
    values: list[IndexValuePoint]


class ArticleIndicesValuesResponse(BaseModel):
    """Historical values for all indices used in an article's cost model"""
    article_id: int
    article_name: str
    indices: list[ArticleIndexData]


class ArticlePricePoint(BaseModel):
    """Single order entry for price history visualisation"""
    order_id: int
    order_date: datetime
    price: float
    price_factor: float
    unit: str


class ArticlePriceHistoryResponse(BaseModel):
    """All order-based price points for an article"""
    article_id: int
    article_name: str
    points: list[ArticlePricePoint]


class ArticleCostBreakdownResponse(BaseModel):
    """Cost contribution breakdown for visualization"""
    article_id: int
    article_name: str
    currency: str = "EUR"
    article_price: Optional[float] = None
    materials_cost: float
    labor_cost: float
    electricity_cost: float
    overhead_cost: float
    profit_margin: float
    total_cost: float


@router.get("/", response_model=list[ArticleRead])
async def list_articles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Article))
    return result.scalars().all()


@router.post("/", response_model=ArticleRead, status_code=status.HTTP_201_CREATED)
async def create_article(
    payload: ArticleCreate, db: AsyncSession = Depends(get_db)
) -> Article:
    article = Article(**payload.model_dump())
    db.add(article)
    await db.commit()
    await db.refresh(article)
    return article


@router.get("/{article_id}/status", response_model=ArticleStatusResponse)
async def get_article_status(
    article_id: int, db: AsyncSession = Depends(get_db)
) -> ArticleStatusResponse:
    """
    Get the processing status of an article.
    
    This is a lightweight endpoint designed for polling to check if 
    background processing (metadata extraction and cost model generation) 
    has completed.
    
    Status values:
    - "pending": Not yet started
    - "processing": Currently processing
    - "completed": Successfully completed
    - "failed": Processing failed (check processing_error)
    """
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    
    return ArticleStatusResponse(
        id=article.id,
        processing_status=article.processing_status,
        processing_error=article.processing_error,
        processing_started_at=article.processing_started_at,
        processing_completed_at=article.processing_completed_at,
    )


@router.get("/{article_id}", response_model=ArticleRead)
async def get_article(
    article_id: int, db: AsyncSession = Depends(get_db)
) -> Article:
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    return article


@router.patch("/{article_id}", response_model=ArticleRead)
async def update_article(
    article_id: int, payload: ArticleUpdate, db: AsyncSession = Depends(get_db)
) -> Article:
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(article, field, value)

    await db.commit()
    await db.refresh(article)
    return article


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(article_id: int, db: AsyncSession = Depends(get_db)) -> None:
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    await db.delete(article)
    await db.commit()


@router.get("/{article_id}/indices-values", response_model=ArticleIndicesValuesResponse)
async def get_article_indices_values(
    article_id: int, db: AsyncSession = Depends(get_db)
) -> ArticleIndicesValuesResponse:
    """
    Get historical values for all indices used in an article's cost model.
    
    Returns time series data for each index/material used in the article,
    suitable for plotting price trends over time.
    """
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    
    # Get all cost models for this article
    cost_models_result = await db.execute(
        select(CostModel)
        .where(CostModel.article_id == article_id)
    )
    cost_models = cost_models_result.scalars().all()
    
    if not cost_models:
        return ArticleIndicesValuesResponse(
            article_id=article.id,
            article_name=article.article_name,
            indices=[]
        )
    
    # Get the unique index IDs used in the cost models
    index_ids = [cm.index_id for cm in cost_models]
    
    # Get the index records to find their names
    current_indices_result = await db.execute(
        select(Index)
        .where(Index.id.in_(index_ids))
    )
    current_indices = current_indices_result.scalars().all()
    
    # Map index names to their quantity + metadata from cost models
    index_meta: dict[str, dict[str, float | str | bool]] = {}
    index_by_id = {idx.id: idx for idx in current_indices}

    for cm in cost_models:
        idx = index_by_id.get(cm.index_id)
        if not idx:
            continue

        is_material = _is_material_unit(idx.unit)
        quantity_unit = "g" if is_material else (idx.unit or "")
        index_meta[idx.name] = {
            "quantity_value": float(cm.part),
            "quantity_unit": quantity_unit,
            "is_material": is_material,
        }
    
    # Get ALL historical values for these index names
    index_names = list(index_meta.keys())
    all_indices_result = await db.execute(
        select(Index)
        .where(Index.name.in_(index_names))
        .order_by(Index.name.asc(), Index.date.asc())
    )
    all_index_records = all_indices_result.scalars().all()
    
    # Group by index name to collect all historical values
    indices_data: dict[str, dict] = {}
    
    for index_record in all_index_records:
        meta = index_meta.get(index_record.name)
        if not meta:
            continue

        quantity_value = float(meta["quantity_value"])
        quantity_unit = str(meta["quantity_unit"])
        is_material = bool(meta["is_material"])

        if index_record.name not in indices_data:
            indices_data[index_record.name] = {
                "index_id": index_record.id,
                "index_name": index_record.name,
                "unit": index_record.unit,
                "quantity_value": quantity_value,
                "quantity_unit": quantity_unit,
                "is_material": is_material,
                "values": []
            }

        quantity_value = indices_data[index_record.name]["quantity_value"]
        value_per_gram = index_record.value_per_gram
        
        # Check if this cost model has a direct EUR value
        cost_model = next((cm for cm in cost_models if cm.index_id == index_record.id), None)
        if cost_model and cost_model.direct_cost_eur is not None:
            # Use direct cost instead of calculating from index
            cost_value = float(cost_model.direct_cost_eur)
        # Compute actual article cost contribution for this index/date
        elif value_per_gram is not None:
            cost_value = float(value_per_gram) * quantity_value
        elif index_record.price_factor and index_record.price_factor != 0:
            # Fallback using unit price / grams factor if value_per_gram missing
            cost_value = (
                float(index_record.value) / float(index_record.price_factor)
            ) * quantity_value
        else:
            # Last resort: use raw unit price
            cost_value = float(index_record.value)

        indices_data[index_record.name]["values"].append(
            IndexValuePoint(
                date=index_record.date,
                value=cost_value,
                unit_value=float(index_record.value),
            )
        )
    
    # Convert to list
    indices_list = [
        ArticleIndexData(**data) 
        for data in indices_data.values()
    ]
    
    return ArticleIndicesValuesResponse(
        article_id=article.id,
        article_name=article.article_name,
        indices=indices_list
    )


@router.get("/{article_id}/cost-breakdown", response_model=ArticleCostBreakdownResponse)
async def get_article_cost_breakdown(
    article_id: int, db: AsyncSession = Depends(get_db)
) -> ArticleCostBreakdownResponse:
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    price_hint = await _latest_article_price(article, db)

    cost_models_result = await db.execute(
        select(CostModel).where(CostModel.article_id == article_id)
    )
    cost_models = cost_models_result.scalars().all()

    materials_cost = 0.0
    labor_cost = 0.0
    electricity_cost = 0.0

    if cost_models:
        index_ids = [cm.index_id for cm in cost_models]
        indices_result = await db.execute(
            select(Index)
            .where(Index.id.in_(index_ids))
            .order_by(Index.id.asc(), Index.date.desc())
        )
        latest_by_id: dict[int, Index] = {}
        for idx in indices_result.scalars():
            if idx.id not in latest_by_id:
                latest_by_id[idx.id] = idx

        for cm in cost_models:
            latest_index = latest_by_id.get(cm.index_id)
            if not latest_index:
                continue

            # Check if this cost model has a direct EUR value
            if cm.direct_cost_eur is not None:
                direct_cost = float(cm.direct_cost_eur)
                
                # Categorize the direct cost based on the index it's associated with
                if latest_index.name == LABOR_INDEX_NAME:
                    labor_cost += direct_cost
                elif latest_index.name == ELECTRICITY_INDEX_NAME:
                    electricity_cost += direct_cost
                else:
                    # Other manufacturing costs - add to materials_cost for now
                    # (could add a separate category if needed)
                    materials_cost += direct_cost
                continue

            # Traditional quantity-based calculation
            quantity = float(cm.part)
            value = float(latest_index.value or 0)

            if latest_index.name == LABOR_INDEX_NAME:
                labor_cost += quantity * value
                continue

            if latest_index.name == ELECTRICITY_INDEX_NAME:
                electricity_cost += quantity * value
                continue

            if latest_index.value_per_gram is not None:
                materials_cost += quantity * float(latest_index.value_per_gram)
            elif latest_index.price_factor and latest_index.price_factor != 0:
                materials_cost += (value / float(latest_index.price_factor)) * quantity
            else:
                materials_cost += value * quantity

    subtotal = materials_cost + labor_cost + electricity_cost
    overhead_cost = subtotal * 0.15
    base_cost = subtotal + overhead_cost

    total_cost = price_hint if price_hint is not None else base_cost
    profit_margin = (
        price_hint - base_cost if price_hint is not None else 0.0
    )

    return ArticleCostBreakdownResponse(
        article_id=article.id,
        article_name=article.article_name,
        article_price=price_hint,
        materials_cost=materials_cost,
        labor_cost=labor_cost,
        electricity_cost=electricity_cost,
        overhead_cost=overhead_cost,
        profit_margin=profit_margin,
        total_cost=total_cost,
    )


@router.get("/{article_id}/price-history", response_model=ArticlePriceHistoryResponse)
async def get_article_price_history(
    article_id: int, db: AsyncSession = Depends(get_db)
) -> ArticlePriceHistoryResponse:
    """
    Return historical price points for the requested article using the orders table.
    Falls back to matching by article_name to support imported CSV data without IDs.
    """
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    orders_result = await db.execute(
        select(Order)
        .where(
            or_(
                Order.article_id == article_id,
                Order.article_name == article.article_name,
            )
        )
        .order_by(Order.order_date.asc())
    )
    orders = orders_result.scalars().all()

    price_points = [
        ArticlePricePoint(
            order_id=order.id,
            order_date=order.order_date,
            price=float(order.price),
            price_factor=float(order.price_factor),
            unit=order.unit,
        )
        for order in orders
    ]

    return ArticlePriceHistoryResponse(
        article_id=article.id,
        article_name=article.article_name,
        points=price_points,
    )
