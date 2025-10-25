from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ArticleBase(BaseModel):
    article_name: str
    description: Optional[str] = None
    unit_weight: Optional[Decimal] = None


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    article_name: Optional[str] = None
    description: Optional[str] = None
    unit_weight: Optional[Decimal] = None


class ArticleRead(ArticleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
