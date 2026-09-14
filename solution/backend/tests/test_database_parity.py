import os
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app import crud
from app.models import Trade
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

POSTGRES_DATABASE_URL = os.getenv("PARITY_DATABASE_URL")


def _fixture_rows() -> list[Trade]:
    return [
        Trade(
            id=101,
            symbol="BTCUSDT",
            strategy="parity",
            side="long",
            opened_at=datetime(2024, 1, 1, 18, 0, tzinfo=UTC),
            closed_at=datetime(2024, 1, 1, 18, 59, 59, tzinfo=UTC),
            qty=Decimal("0.12500000"),
            entry_price=Decimal("100.00"),
            exit_price=Decimal("110.00"),
            fee=Decimal("0.25"),
            pnl=Decimal("9.75"),
        ),
        Trade(
            id=102,
            symbol="ETHUSDT",
            strategy="parity",
            side="short",
            opened_at=datetime(2024, 1, 2, 18, 0, tzinfo=UTC),
            closed_at=datetime(2024, 1, 1, 19, 0, tzinfo=UTC),
            qty=Decimal("1.00000000"),
            entry_price=Decimal("200.00"),
            exit_price=Decimal("198.00"),
            fee=Decimal("0.10"),
            pnl=Decimal("-2.10"),
        ),
        Trade(
            id=103,
            symbol="BTCUSDT",
            strategy="parity",
            side="long",
            opened_at=datetime(2024, 1, 4, 18, 0, tzinfo=UTC),
            closed_at=datetime(2024, 1, 4, 19, 0, tzinfo=UTC),
            qty=Decimal("0.50000000"),
            entry_price=Decimal("100.00"),
            exit_price=Decimal("100.00"),
            fee=Decimal("0.00"),
            pnl=Decimal("0.00"),
        ),
    ]


def _stats_for_url(database_url: str) -> dict[str, object]:
    engine_kwargs = (
        {"connect_args": {"check_same_thread": False}} if database_url.startswith("sqlite") else {}
    )
    engine = create_engine(database_url, **engine_kwargs)
    Trade.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            session.query(Trade).delete(synchronize_session=False)
            session.add_all(_fixture_rows())
            session.commit()
            return crud.get_trade_stats(session)
    finally:
        Trade.metadata.drop_all(engine)
        engine.dispose()


@pytest.mark.skipif(
    not POSTGRES_DATABASE_URL,
    reason="PARITY_DATABASE_URL is required for SQLite/PostgreSQL parity",
)
def test_stats_match_between_sqlite_and_postgresql():
    sqlite_stats = _stats_for_url("sqlite:///:memory:")
    postgres_stats = _stats_for_url(POSTGRES_DATABASE_URL)

    assert postgres_stats == sqlite_stats


@pytest.mark.skipif(
    not POSTGRES_DATABASE_URL,
    reason="PARITY_DATABASE_URL is required for SQLite/PostgreSQL parity",
)
def test_filtered_trades_match_between_sqlite_and_postgresql():
    sqlite_engine = create_engine("sqlite:///:memory:")
    postgres_engine = create_engine(POSTGRES_DATABASE_URL)
    try:
        results: list[list[tuple[int, str]]] = []
        for engine in (sqlite_engine, postgres_engine):
            Trade.metadata.create_all(engine)
            with Session(engine) as session:
                session.add_all(_fixture_rows())
                session.commit()
                trades, total = crud.get_trades(
                    session,
                    symbols=["BTCUSDT"],
                    date_from=datetime(2024, 1, 1).date(),
                    date_to=datetime(2024, 1, 5).date(),
                    sort_by="pnl",
                    order="asc",
                )
                results.append([(trade.id, str(trade.pnl)) for trade in trades])
                assert total == 2
        assert results[0] == results[1]
    finally:
        Trade.metadata.drop_all(sqlite_engine)
        Trade.metadata.drop_all(postgres_engine)
        sqlite_engine.dispose()
        postgres_engine.dispose()
