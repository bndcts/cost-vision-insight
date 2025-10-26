from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.article import ArticleRead
from app.schemas.index import IndexRead


class CostModelBase(BaseModel):
    article_id: int
    index_id: int
    part: Decimal  # quantity attributed to this index (grams, hours, etc.)
    direct_cost_eur: Optional[Decimal] = None  # direct EUR cost (overrides part * index_value)


class CostModelCreate(CostModelBase):
    pass


class CostModelUpdate(BaseModel):
    part: Optional[Decimal] = None
    direct_cost_eur: Optional[Decimal] = None


class CostModelRead(CostModelBase):
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    article: Optional[ArticleRead] = None
    index: Optional[IndexRead] = None
