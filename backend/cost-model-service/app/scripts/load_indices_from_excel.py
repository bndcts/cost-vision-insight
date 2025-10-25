from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

import pandas as pd
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.index import Index

DECIMAL_PLACES = Decimal("0.000001")
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
    value: Decimal
    value_per_gram: Decimal
    date: date
    price_factor: Decimal
    unit: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load TAC index data from an Excel workbook into the database."
    )
    parser.add_argument(
        "--file",
        required=True,
        type=Path,
        help="Path to the Excel workbook (e.g. 20250730_TAC_Index_data_cbl.xlsx).",
    )
    parser.add_argument(
        "--skip-sheets",
        type=int,
        default=1,
        help="Number of leading sheets to skip (default: 1, skips the summary sheet).",
    )
    return parser.parse_args()


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_PLACES)


def _extract_unit(column_name: str) -> str:
    if "[" in column_name and "]" in column_name:
        chunk = column_name.split("[", 1)[1].split("]", 1)[0]
    else:
        chunk = column_name
    chunk = chunk.replace("€", "").replace("/", "").replace("{", "").replace("}", "")
    unit = chunk.strip().lower()
    if not unit:
        raise ValueError(f"Could not extract unit from column '{column_name}'")
    return unit


def _grams_for_unit(unit: str) -> Decimal:
    normalized = unit.lower()
    if normalized not in UNIT_TO_GRAMS:
        raise ValueError(f"Unsupported unit '{unit}'. Add it to UNIT_TO_GRAMS.")
    return UNIT_TO_GRAMS[normalized]


def _parse_date(value) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return datetime.strptime(value.strip(), "%d.%m.%Y").date()
    return pd.to_datetime(value).date()


def _price_column(columns: Iterable[str]) -> str | None:
    for column in columns:
        if column.lower().startswith("tac -"):
            return column
    return None


def build_records(workbook: Path, skip_sheets: int) -> list[IndexRecord]:
    if not workbook.exists():
        raise FileNotFoundError(workbook)

    xls = pd.ExcelFile(workbook)
    sheet_names = xls.sheet_names[skip_sheets:]
    records: list[IndexRecord] = []

    for sheet in sheet_names:
        frame = pd.read_excel(xls, sheet_name=sheet)
        if "Datum" not in frame.columns:
            print(f"Skipping sheet '{sheet}' (missing 'Datum' column).")
            continue

        price_column = _price_column(frame.columns)
        if not price_column:
            print(f"Skipping sheet '{sheet}' (missing TAC price column).")
            continue

        try:
            unit = _extract_unit(price_column)
            grams_per_unit = _grams_for_unit(unit)
        except ValueError as exc:
            print(f"Skipping sheet '{sheet}': {exc}")
            continue

        for _, row in frame.iterrows():
            date_cell = row.get("Datum")
            price_cell = row.get(price_column)
            if pd.isna(date_cell) or pd.isna(price_cell):
                continue

            try:
                parsed_date = _parse_date(date_cell)
                price_value = Decimal(str(price_cell))
            except (ValueError, InvalidOperation):
                continue

            normalized_price = _quantize(price_value)
            price_per_gram = _quantize(price_value / grams_per_unit)

            records.append(
                IndexRecord(
                    name=str(sheet).strip(),
                    value=normalized_price,
                    value_per_gram=price_per_gram,
                    date=parsed_date,
                    price_factor=grams_per_unit,
                    unit=unit,
                )
            )

    return records


async def upsert_indices(records: list[IndexRecord]) -> None:
    if not records:
        print("No records to insert.")
        return

    async with SessionLocal() as session:
        for entry in records:
            stmt = select(Index).where(
                Index.name == entry.name,
                Index.date == entry.date,
            )
            result = await session.execute(stmt)
            index = result.scalars().first()

            payload = {
                "name": entry.name,
                "value": entry.value,
                "value_per_gram": entry.value_per_gram,
                "date": entry.date,
                "price_factor": entry.price_factor,
                "unit": entry.unit,
            }

            if index:
                for field, value in payload.items():
                    setattr(index, field, value)
            else:
                session.add(Index(**payload))

        await session.commit()

    print(f"Upserted {len(records)} index rows.")


def main() -> None:
    args = parse_args()
    records = build_records(args.file, args.skip_sheets)
    asyncio.run(upsert_indices(records))


if __name__ == "__main__":
    main()
