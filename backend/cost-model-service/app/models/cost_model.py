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
    # part stores the quantity associated with this index (grams, hours, MWh, ...)
    # For material indices, this is the quantity. For direct cost entries, this can be 0 or 1.
    part: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    # direct_cost_eur: when set, this is a direct EUR cost (not quantity * index_value)
    # Used for AI-estimated labor, electricity, and other manufacturing costs
    direct_cost_eur: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    article: Mapped["Article"] = relationship(back_populates="cost_models")
    index: Mapped["Index"] = relationship(back_populates="cost_models")
