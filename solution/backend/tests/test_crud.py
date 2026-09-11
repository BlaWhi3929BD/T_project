from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app import crud
from app.database import Base
from app.models import Trade
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(
            [
                Trade(
                    id=1,
                    symbol="BTCUSDT",
                    strategy="test",
                    side="long",
                    opened_at=datetime(2024, 1, 1, tzinfo=UTC),
                    closed_at=datetime(2024, 1, 1, 18, 59, 59, tzinfo=UTC),
                    qty=Decimal("1"),
                    entry_price=Decimal("100"),
                    exit_price=Decimal("110"),
                    fee=Decimal("0"),
                    pnl=Decimal("10.00"),
                ),
                Trade(
                    id=2,
                    symbol="BTCUSDT",
                    strategy="test",
                    side="short",
                    opened_at=datetime(2024, 1, 1, tzinfo=UTC),
                    closed_at=datetime(2024, 1, 1, 19, 0, 0, tzinfo=UTC),
                    qty=Decimal("1"),
                    entry_price=Decimal("100"),
                    exit_price=Decimal("103"),
                    fee=Decimal("0"),
                    pnl=Decimal("-3.00"),
                ),
                Trade(
                    id=3,
                    symbol="ETHUSDT",
                    strategy="test",
                    side="long",
                    opened_at=datetime(2024, 1, 1, tzinfo=UTC),
                    closed_at=datetime(2024, 1, 4, 12, 0, tzinfo=UTC),
                    qty=Decimal("1"),
                    entry_price=Decimal("100"),
                    exit_price=Decimal("100"),
                    fee=Decimal("0"),
                    pnl=Decimal("0.00"),
                ),
                Trade(
                    id=4,
                    symbol="ETHUSDT",
                    strategy="test",
                    side="long",
                    opened_at=datetime(2024, 1, 1, tzinfo=UTC),
                    closed_at=datetime(2024, 1, 4, 13, 0, tzinfo=UTC),
                    qty=Decimal("1"),
                    entry_price=Decimal("100"),
                    exit_price=Decimal("102"),
                    fee=Decimal("0"),
                    pnl=Decimal("2.00"),
                ),
            ]
        )
        session.commit()
        yield session


def test_stats_formulas_and_continuous_curve(db):
    stats = crud.get_trade_stats(db)

    assert stats["trades_count"] == 4
    assert stats["wins"] == 2
    assert stats["losses"] == 1
    assert stats["breakeven"] == 1
    assert stats["net_pnl"] == "9.00"
    assert stats["gross_profit"] == "12.00"
    assert stats["gross_loss"] == "3.00"
    assert stats["avg_win"] == "6.00"
    assert stats["avg_loss"] == "-3.00"
    assert stats["profit_factor"] == 4.0
    assert [point["date"] for point in stats["equity_curve"]] == [
        "2024-01-01",
        "2024-01-02",
        "2024-01-03",
        "2024-01-04",
    ]
    assert stats["equity_curve"][1]["day_pnl"] == "-3.00"
    assert stats["equity_curve"][2]["day_pnl"] == "0.00"
    assert stats["max_drawdown"] == "3.00"


def test_date_filter_uses_almaty_day_boundary(db):
    day = datetime(2024, 1, 2).date()
    stats = crud.get_trade_stats(db, date_from=day, date_to=day)

    assert stats["trades_count"] == 1
    assert stats["net_pnl"] == "-3.00"


def test_empty_stats_have_null_ratios(db):
    stats = crud.get_trade_stats(db, symbols=["MISSING"])

    assert stats["trades_count"] == 0
    assert stats["net_pnl"] == "0.00"
    assert stats["win_rate"] is None
    assert stats["profit_factor"] is None
    assert stats["avg_win"] is None
    assert stats["avg_loss"] is None
    assert stats["equity_curve"] == []


def test_pagination_is_deterministic_for_equal_dates(db):
    first_page, total = crud.get_trades(
        db,
        sort_by="closed_at",
        order="asc",
        page=1,
        page_size=2,
    )
    second_page, _ = crud.get_trades(
        db,
        sort_by="closed_at",
        order="asc",
        page=2,
        page_size=2,
    )

    assert total == 4
    assert [trade.id for trade in first_page] == [1, 2]
    assert [trade.id for trade in second_page] == [3, 4]
