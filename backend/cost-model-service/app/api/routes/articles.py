from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, date

from app.api.deps import get_db
from app.models.article import Article
from app.models.cost_model import CostModel
from app.models.index import Index
from app.schemas.article import ArticleCreate, ArticleRead, ArticleUpdate

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


class ArticleIndexData(BaseModel):
    """Time series data for a single index used in an article"""
    index_id: int
    index_name: str
    unit: str
    quantity_grams: float
    values: list[IndexValuePoint]


class ArticleIndicesValuesResponse(BaseModel):
    """Historical values for all indices used in an article's cost model"""
    article_id: int
    article_name: str
    indices: list[ArticleIndexData]


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
    
    # Map index names to their quantity_grams from cost models
    index_name_to_quantity: dict[str, float] = {}
    for cm in cost_models:
        for idx in current_indices:
            if idx.id == cm.index_id:
                index_name_to_quantity[idx.name] = float(cm.part)
                break
    
    # Get ALL historical values for these index names
    index_names = list(index_name_to_quantity.keys())
    all_indices_result = await db.execute(
        select(Index)
        .where(Index.name.in_(index_names))
        .order_by(Index.name.asc(), Index.date.asc())
    )
    all_index_records = all_indices_result.scalars().all()
    
    # Group by index name to collect all historical values
    indices_data: dict[str, dict] = {}
    
    for index_record in all_index_records:
        if index_record.name not in indices_data:
            indices_data[index_record.name] = {
                "index_id": index_record.id,
                "index_name": index_record.name,
                "unit": index_record.unit,
                "quantity_grams": index_name_to_quantity[index_record.name],
                "values": []
            }
        
        indices_data[index_record.name]["values"].append(
            IndexValuePoint(
                date=index_record.date,
                value=float(index_record.value)
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
