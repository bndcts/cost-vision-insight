from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class IndexBase(BaseModel):
    name: str
    value: Decimal
    value_per_gram: Decimal
    date: date
    price_factor: Decimal
    unit: str


class IndexCreate(IndexBase):
    pass


class IndexUpdate(BaseModel):
    value: Optional[Decimal] = None
    value_per_gram: Optional[Decimal] = None
    date: Optional[date] = None
    price_factor: Optional[Decimal] = None
    unit: Optional[str] = None


class IndexRead(IndexBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
