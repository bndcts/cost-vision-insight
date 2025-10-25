from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ArticleBase(BaseModel):
    article_name: str
    description: Optional[str] = None
    unit_weight: Optional[Decimal] = None


class ArticleCreate(ArticleBase):
    product_specification_file: Optional[bytes] = None
    product_specification_filename: Optional[str] = None
    drawing_file: Optional[bytes] = None
    drawing_filename: Optional[str] = None
    comment: Optional[str] = None


class ArticleUpdate(BaseModel):
    article_name: Optional[str] = None
    description: Optional[str] = None
    unit_weight: Optional[Decimal] = None
    product_specification_file: Optional[bytes] = None
    product_specification_filename: Optional[str] = None
    drawing_file: Optional[bytes] = None
    drawing_filename: Optional[str] = None
    comment: Optional[str] = None


class ArticleRead(ArticleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_specification_filename: Optional[str] = None
    drawing_filename: Optional[str] = None
    comment: Optional[str] = None
    processing_status: str
    processing_error: Optional[str] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    created_at: datetime
    # Note: file data (bytes) is excluded from read responses for performance
    # Use a separate endpoint to download the actual files
