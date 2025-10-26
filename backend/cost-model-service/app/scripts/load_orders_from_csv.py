from __future__ import annotations

import argparse
import asyncio
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.article import Article
from app.models.order import Order


@dataclass(slots=True)
class OrderRecord:
    article_name: str
    price: Decimal
    price_factor: Decimal
    unit: str
    order_date: datetime


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load synthetic order data from CSV.")
    parser.add_argument(
        "--file",
        required=True,
        type=Path,
        help="Absolute path to synthetic_orders.csv",
    )
    return parser.parse_args()


def _parse_decimal(value: str | None) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        return Decimal(value.strip())
    except (InvalidOperation, AttributeError):
        return None


def _parse_datetime(value: str | None) -> Optional[datetime]:
    if value is None:
        return None
    try:
        dt = datetime.fromisoformat(value.strip())
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def build_records(csv_path: Path) -> list[OrderRecord]:
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    records: list[OrderRecord] = []

    with csv_path.open("r", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            article_name = (row.get("article_name") or "").strip()
            price = _parse_decimal(row.get("price"))
            price_factor = _parse_decimal(row.get("price_factor"))
            unit = (row.get("unit") or "").strip()
            order_date = _parse_datetime(row.get("order_date"))

            if (
                not article_name
                or price is None
                or price_factor is None
                or not unit
                or order_date is None
            ):
                continue

            records.append(
                OrderRecord(
                    article_name=article_name,
                    price=price,
                    price_factor=price_factor,
                    unit=unit,
                    order_date=order_date,
                )
            )

    return records


async def upsert(records: list[OrderRecord]) -> None:
    if not records:
        print("No order rows parsed; skipping import.")
        return

    async with SessionLocal() as session:
        article_cache: dict[str, Optional[int]] = {}

        for entry in records:
            if entry.article_name not in article_cache:
                stmt = select(Article.id).where(Article.article_name == entry.article_name)
                result = await session.execute(stmt)
                article_cache[entry.article_name] = result.scalars().first()

            stmt = select(Order).where(
                Order.article_name == entry.article_name,
                Order.order_date == entry.order_date,
                Order.price == entry.price,
            )
            result = await session.execute(stmt)
            existing = result.scalars().first()

            payload = {
                "article_id": article_cache.get(entry.article_name),
                "article_name": entry.article_name,
                "price": entry.price,
                "price_factor": entry.price_factor,
                "unit": entry.unit,
                "order_date": entry.order_date,
            }

            if existing:
                for field, value in payload.items():
                    setattr(existing, field, value)
            else:
                session.add(Order(**payload))

        await session.commit()

    print(f"Upserted {len(records)} order rows from CSV.")


def main() -> None:
    args = parse_args()
    records = build_records(args.file)
    asyncio.run(upsert(records))


if __name__ == "__main__":
    main()
