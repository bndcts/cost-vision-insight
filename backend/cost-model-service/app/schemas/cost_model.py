from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.article import ArticleRead
from app.schemas.index import IndexRead


class CostModelBase(BaseModel):
    article_id: int
    index_id: int
    part: Decimal  # grams attributed to this index


class CostModelCreate(CostModelBase):
    pass


class CostModelUpdate(BaseModel):
    part: Optional[Decimal] = None


class CostModelRead(CostModelBase):
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    article: Optional[ArticleRead] = None
    index: Optional[IndexRead] = None
