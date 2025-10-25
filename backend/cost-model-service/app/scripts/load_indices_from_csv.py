from __future__ import annotations

import argparse
import asyncio
import csv
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.index import Index

DECIMAL_PLACES = Decimal("0.000001")
UNIT_PATTERN = re.compile(r"\[([^\]]+)\]")
UNIT_TO_GRAMS = {
    "g": Decimal("1"),
    "gram": Decimal("1"),
    "grams": Decimal("1"),
    "kg": Decimal("1000"),
    "kilogram": Decimal("1000"),
    "kilograms": Decimal("1000"),
    "t": Decimal("1000000"),
    "ton": Decimal("1000000"),
    "tons": Decimal("1000000"),
    "tonne": Decimal("1000000"),
    "tonnes": Decimal("1000000"),
}


@dataclass
class IndexRecord:
    name: str
    date: date
    value: Decimal
    unit: str
    price_factor: Decimal
    value_per_gram: Optional[Decimal]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load TAC index data from CSV.")
    parser.add_argument(
        "--file",
        required=True,
        type=Path,
        help="Absolute path to indices.csv",
    )
    return parser.parse_args()


def _parse_date(value: str) -> date:
    value = value.strip()
    # Expected format DD.MM.YYYY
    return datetime.strptime(value, "%d.%m.%Y").date()


def _parse_numeric(value: str) -> Optional[Decimal]:
    if value is None:
        return None

    cleaned = value.strip().replace("\u00a0", "")
    if cleaned in {"", "-"}:
        return None

    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _base_unit(column_name: str) -> tuple[str, Optional[Decimal]]:
    match = UNIT_PATTERN.search(column_name)
    if not match:
        return "", None

    bracket = match.group(1)
    _, _, tail = bracket.partition("/")
    unit = tail or bracket
    normalized = unit.strip().lower()
    grams_factor = UNIT_TO_GRAMS.get(normalized)
    return normalized, grams_factor


def build_records(csv_path: Path) -> list[IndexRecord]:
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    records: list[IndexRecord] = []

    with csv_path.open("r", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        date_column = None
        for field in reader.fieldnames or []:
            lowered = field.lower()
            if lowered in {"date", "datum"}:
                date_column = field
                break

        if not date_column:
            raise ValueError("CSV must include a Date column.")

        data_columns = [
            col for col in reader.fieldnames or [] if col != date_column
        ]

        unit_cache: dict[str, tuple[str, Optional[Decimal]]] = {}

        for row in reader:
            raw_date = row.get(date_column)
            if not raw_date or not raw_date.strip():
                continue

            try:
                parsed_date = _parse_date(raw_date)
            except ValueError:
                continue

            for column in data_columns:
                raw_value = row.get(column)
                numeric = _parse_numeric(raw_value) if raw_value is not None else None
                if numeric is None:
                    continue

                if column not in unit_cache:
                    unit_cache[column] = _base_unit(column)

                unit_name, grams_factor = unit_cache[column]

                value_per_gram = (
                    (numeric / grams_factor).quantize(DECIMAL_PLACES)
                    if grams_factor
                    else None
                )

                records.append(
                    IndexRecord(
                        name=column.strip(),
                        date=parsed_date,
                        value=numeric.quantize(DECIMAL_PLACES),
                        unit=unit_name or "",
                        price_factor=grams_factor or Decimal("1"),
                        value_per_gram=value_per_gram,
                    )
                )

    return records


async def upsert(records: list[IndexRecord]) -> None:
    if not records:
        print("No index rows parsed; skipping import.")
        return

    async with SessionLocal() as session:
        for entry in records:
            stmt = select(Index).where(
                Index.name == entry.name,
                Index.date == entry.date,
            )
            result = await session.execute(stmt)
            existing = result.scalars().first()

            payload = {
                "name": entry.name,
                "date": entry.date,
                "value": entry.value,
                "unit": entry.unit,
                "price_factor": entry.price_factor,
                "value_per_gram": entry.value_per_gram,
            }

            if existing:
                for field, value in payload.items():
                    setattr(existing, field, value)
            else:
                session.add(Index(**payload))

        await session.commit()

    print(f"Upserted {len(records)} index rows from CSV.")


def main() -> None:
    args = parse_args()
    records = build_records(args.file)
    asyncio.run(upsert(records))


if __name__ == "__main__":
    main()
