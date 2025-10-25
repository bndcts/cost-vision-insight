from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.article import Article
from app.schemas.article import ArticleCreate, ArticleRead, ArticleUpdate

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("/", response_model=list[ArticleRead])
async def list_articles(db: AsyncSession = Depends(get_db)) -> list[Article]:
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
