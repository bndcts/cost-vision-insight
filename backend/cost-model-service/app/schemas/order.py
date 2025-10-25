from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class OrderBase(BaseModel):
    article_id: Optional[int] = None
    article_name: str
    price: Decimal
    price_factor: Decimal
    unit: str
    order_date: datetime


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    article_id: Optional[int] = None
    article_name: Optional[str] = None
    price: Optional[Decimal] = None
    price_factor: Optional[Decimal] = None
    unit: Optional[str] = None
    order_date: Optional[datetime] = None


class OrderRead(OrderBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
