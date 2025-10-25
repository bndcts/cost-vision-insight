from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional

from app.db.base import Base


if TYPE_CHECKING:
    from app.models.article import Article


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    article_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("articles.id", ondelete="SET NULL"), nullable=True
    )
    article_name: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    price_factor: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    unit: Mapped[str] = mapped_column(String(64), nullable=False)
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    article: Mapped[Optional["Article"]] = relationship(back_populates="orders")
