from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import DateTime, LargeBinary, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional

from app.db.base import Base


if TYPE_CHECKING:
    from app.models.cost_model import CostModel
    from app.models.order import Order


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    article_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    unit_weight: Mapped[Optional[float]] = mapped_column(Numeric(18, 6), nullable=True)
    product_specification_file: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    product_specification_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    drawing_file: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    drawing_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Processing status fields
    processing_status: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        default="pending",
        # Values: "pending", "processing", "completed", "failed"
    )
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Similar articles found via Weaviate vector search
    similar_articles: Mapped[Optional[list[int]]] = mapped_column(
        ARRAY(sa.Integer),
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    cost_models: Mapped[list["CostModel"]] = relationship(
        back_populates="article", cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship(
        back_populates="article", cascade="all, delete-orphan"
    )
