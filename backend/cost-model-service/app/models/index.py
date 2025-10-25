from datetime import datetime, timezone

from sqlalchemy import Date, DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.db.base import Base


if TYPE_CHECKING:
    from app.models.cost_model import CostModel


class Index(Base):
    __tablename__ = "indices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    value: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    price_factor: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    unit: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    cost_models: Mapped[list["CostModel"]] = relationship(
        back_populates="index", cascade="all, delete-orphan"
    )
