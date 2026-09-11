"""Load the deterministic trade dataset into the configured database."""

from __future__ import annotations

import argparse
import csv
import hashlib
import logging
import os
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from app.database import SessionLocal, create_db_and_tables
from app.models import Trade
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

DEFAULT_CSV_PATH = "/app/task/data/trades.csv"
LOCK_KEY = int.from_bytes(hashlib.sha256(b"trades-dashboard-seed").digest()[:8], "big", signed=True)
DECIMAL_FIELDS = ("qty", "entry_price", "exit_price", "fee", "pnl")
DATABASE_RETRY_ATTEMPTS = int(os.getenv("DATABASE_RETRY_ATTEMPTS", "60"))
DATABASE_RETRY_DELAY = float(os.getenv("DATABASE_RETRY_DELAY", "2"))
logger = logging.getLogger(__name__)


def csv_path_from_environment() -> Path:
    return Path(os.getenv("CSV_PATH", DEFAULT_CSV_PATH))


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(UTC)


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

    for attempt in range(1, DATABASE_RETRY_ATTEMPTS + 1):
        db = SessionLocal()
        try:
            seed_database(
                db,
                csv_path=args.csv_path,
                if_empty=args.if_empty or not args.force,
                force=args.force,
            )
            return
        except OperationalError as error:
            db.rollback()
            if getattr(error.orig, "pgcode", None) == "28P01":
                raise
            if attempt >= DATABASE_RETRY_ATTEMPTS:
                raise
            logger.warning(
                "Database is not ready; retrying in %.1f seconds (%d/%d)",
                DATABASE_RETRY_DELAY,
                attempt,
                DATABASE_RETRY_ATTEMPTS,
            )
            time.sleep(DATABASE_RETRY_DELAY)
        finally:
            db.close()


if __name__ == "__main__":
    main()
