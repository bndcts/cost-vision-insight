from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.index import Index
from app.schemas.index import IndexCreate, IndexRead, IndexUpdate

router = APIRouter(prefix="/indices", tags=["indices"])


@router.get("/", response_model=list[IndexRead])
async def list_indices(db: AsyncSession = Depends(get_db)) -> list[Index]:
    result = await db.execute(select(Index).order_by(Index.date.desc()))
    return result.scalars().all()


@router.post("/", response_model=IndexRead, status_code=status.HTTP_201_CREATED)
async def create_index(
    payload: IndexCreate, db: AsyncSession = Depends(get_db)
) -> Index:
    index = Index(**payload.model_dump())
    db.add(index)
    await db.commit()
    await db.refresh(index)
    return index


@router.get("/{index_id}", response_model=IndexRead)
async def get_index(index_id: int, db: AsyncSession = Depends(get_db)) -> Index:
    index = await db.get(Index, index_id)
    if not index:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Index not found")
    return index


@router.patch("/{index_id}", response_model=IndexRead)
async def update_index(
    index_id: int, payload: IndexUpdate, db: AsyncSession = Depends(get_db)
) -> Index:
    index = await db.get(Index, index_id)
    if not index:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Index not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(index, field, value)

    await db.commit()
    await db.refresh(index)
    return index


@router.delete("/{index_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_index(index_id: int, db: AsyncSession = Depends(get_db)) -> None:
    index = await db.get(Index, index_id)
    if not index:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Index not found")

    await db.delete(index)
    await db.commit()
