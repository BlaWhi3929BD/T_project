"""Load the deterministic trade dataset into the configured database."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Iterator

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import SessionLocal, create_db_and_tables
from app.models import Trade

DEFAULT_CSV_PATH = "/app/task/data/trades.csv"
LOCK_KEY = int.from_bytes(hashlib.sha256(b"trades-dashboard-seed").digest()[:8], "big", signed=True)
DECIMAL_FIELDS = ("qty", "entry_price", "exit_price", "fee", "pnl")


def csv_path_from_environment() -> Path:
    return Path(os.getenv("CSV_PATH", DEFAULT_CSV_PATH))


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(timezone.utc)


def _read_rows(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        raise FileNotFoundError(f"CSV dataset not found: {path}")

    rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "id": int(row["id"]),
                    "symbol": row["symbol"],
                    "strategy": row["strategy"],
                    "side": row["side"],
                    "opened_at": _parse_datetime(row["opened_at"]),
                    "closed_at": _parse_datetime(row["closed_at"]),
                    **{field: Decimal(row[field]) for field in DECIMAL_FIELDS},
                }
            )
    if not rows:
        raise ValueError(f"CSV dataset is empty: {path}")
    return rows


@contextmanager
def _seed_lock(db: Session) -> Iterator[None]:
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": LOCK_KEY})
    yield


def seed_database(
    db: Session,
    csv_path: Path | str | None = None,
    *,
    if_empty: bool = True,
    force: bool = False,
) -> bool:
    """Load the dataset atomically, returning whether rows were inserted."""
    if force and if_empty:
        raise ValueError("--force and --if-empty cannot be used together")

    create_db_and_tables()
    path = Path(csv_path) if csv_path is not None else csv_path_from_environment()
    rows = _read_rows(path)

    with _seed_lock(db):
        current_count = db.query(Trade).count()
        if if_empty and current_count == len(rows):
            print(f"Table trades already contains {current_count} rows. Skipping seed.")
            return False
        if if_empty and current_count != 0:
            print(f"Table trades contains {current_count} of {len(rows)} rows. Reloading.")

        try:
            if force or current_count:
                db.query(Trade).delete(synchronize_session=False)
            db.bulk_insert_mappings(Trade, rows)
            db.commit()
        except Exception:
            db.rollback()
            raise

    print(f"Loaded {len(rows)} trades from {path}.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--if-empty", action="store_true", help="Skip a complete existing dataset")
    mode.add_argument("--force", action="store_true", help="Replace all existing rows")
    parser.add_argument("--csv-path", type=Path, default=None)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        seed_database(
            db,
            csv_path=args.csv_path,
            if_empty=args.if_empty or not args.force,
            force=args.force,
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
