from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.db.base import Base


if TYPE_CHECKING:
    from app.models.article import Article
    from app.models.index import Index


class CostModel(Base):
    __tablename__ = "cost_models"

    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True
    )
    index_id: Mapped[int] = mapped_column(
        ForeignKey("indices.id", ondelete="CASCADE"), primary_key=True
    )
    part: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    article: Mapped["Article"] = relationship(back_populates="cost_models")
    index: Mapped["Index"] = relationship(back_populates="cost_models")
