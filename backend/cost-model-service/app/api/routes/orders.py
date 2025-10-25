from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.article import Article
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderRead, OrderUpdate

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/", response_model=list[OrderRead])
async def list_orders(db: AsyncSession = Depends(get_db)) -> list[Order]:
    result = await db.execute(select(Order).order_by(Order.order_date.desc()))
    return result.scalars().all()


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate, db: AsyncSession = Depends(get_db)
) -> Order:
    if payload.article_id is not None:
        article = await db.get(Article, payload.article_id)
        if not article:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

        # if article_id provided but article_name missing, fallback to stored name
        if not payload.article_name:
            payload.article_name = article.article_name

    order = Order(**payload.model_dump())
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)) -> Order:
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.patch("/{order_id}", response_model=OrderRead)
async def update_order(
    order_id: int, payload: OrderUpdate, db: AsyncSession = Depends(get_db)
) -> Order:
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(order, field, value)

    await db.commit()
    await db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(order_id: int, db: AsyncSession = Depends(get_db)) -> None:
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    await db.delete(order)
    await db.commit()
