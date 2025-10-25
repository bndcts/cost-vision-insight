from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.api.deps import get_db
from app.models.article import Article
from app.schemas.article import ArticleCreate, ArticleRead, ArticleUpdate

router = APIRouter(prefix="/articles", tags=["articles"])


class ArticleStatusResponse(BaseModel):
    """Lightweight response for polling article processing status"""
    id: int
    processing_status: str
    processing_error: Optional[str] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None


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
