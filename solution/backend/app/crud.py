from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.models import Trade
from app.schemas import TradeCreate
from sqlalchemy import asc, case, desc, func, literal_column
from sqlalchemy.orm import Session

# The dataset and task contract define Almaty as UTC+5 without DST.
ALMATY_TZ = timezone(timedelta(hours=5))
UTC = UTC
CENT = Decimal("0.01")
MAX_FILTER_VALUES = 100


def _utc_boundary(value: date, *, end: bool = False) -> datetime:
    local = datetime.combine(value + (timedelta(days=1) if end else timedelta()), time.min)
    return local.replace(tzinfo=ALMATY_TZ).astimezone(UTC)


def _apply_filters(
    query: Any,
    *,
    symbols: list[str] | None = None,
    strategies: list[str] | None = None,
    side: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> Any:
    if symbols:
        query = query.filter(Trade.symbol.in_(symbols))
    if strategies:
        query = query.filter(Trade.strategy.in_(strategies))
    if side:
        query = query.filter(Trade.side == side)
    if date_from:
        query = query.filter(Trade.closed_at >= _utc_boundary(date_from))
    if date_to:
        query = query.filter(Trade.closed_at < _utc_boundary(date_to, end=True))
    return query


def create_trade(db: Session, trade: TradeCreate) -> Trade:
    db_trade = Trade(
        symbol=trade.symbol,
        strategy=trade.strategy,
        side=trade.side,
        opened_at=trade.opened_at,
        closed_at=trade.closed_at,
        qty=Decimal(trade.qty),
        entry_price=Decimal(trade.entry_price),
        exit_price=Decimal(trade.exit_price),
        fee=Decimal(trade.fee),
        pnl=Decimal(trade.pnl),
    )
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade


def get_trades(
    db: Session,
    *,
    symbols: list[str] | None = None,
    strategies: list[str] | None = None,
    side: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    sort_by: str = "closed_at",
    order: str = "desc",
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Trade], int]:
    query = _apply_filters(
        db.query(Trade),
        symbols=symbols,
        strategies=strategies,
        side=side,
        date_from=date_from,
        date_to=date_to,
    )
    total_trades = query.count()
    sort_column = getattr(Trade, sort_by, Trade.closed_at)
    query = query.order_by(
        (asc(sort_column) if order == "asc" else desc(sort_column)),
        asc(Trade.id),
    )
    trades = query.offset((page - 1) * page_size).limit(page_size).all()
    return trades, total_trades


def get_filter_options(db: Session) -> tuple[list[str], list[str]]:
    symbols = [row[0] for row in db.query(Trade.symbol).distinct().order_by(Trade.symbol)]
    strategies = [row[0] for row in db.query(Trade.strategy).distinct().order_by(Trade.strategy)]
    return symbols, strategies


def _day_expression(db: Session) -> Any:
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        return literal_column("((closed_at AT TIME ZONE 'UTC') + INTERVAL '5 hours')::date")
    return func.date(Trade.closed_at, "+5 hours")


def _money(value: Any) -> Decimal:
    return Decimal(str(value or 0))


def _format_money(value: Any) -> str:
    return str(_money(value).quantize(CENT, ROUND_HALF_UP))


def _empty_stats() -> dict[str, Any]:
    return {
        "trades_count": 0,
        "wins": 0,
        "losses": 0,
        "breakeven": 0,
        "net_pnl": "0.00",
        "gross_profit": "0.00",
        "gross_loss": "0.00",
        "win_rate": None,
        "profit_factor": None,
        "avg_win": None,
        "avg_loss": None,
        "best_trade": "0.00",
        "worst_trade": "0.00",
        "max_drawdown": "0.00",
        "equity_curve": [],
    }


def get_trade_stats(
    db: Session,
    *,
    symbols: list[str] | None = None,
    strategies: list[str] | None = None,
    side: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> dict[str, Any]:
    query = _apply_filters(
        db.query(Trade),
        symbols=symbols,
        strategies=strategies,
        side=side,
        date_from=date_from,
        date_to=date_to,
    )
    daily_rows = (
        query.with_entities(
            _day_expression(db).label("day"),
            func.count(Trade.id).label("trades_count"),
            func.sum(case((Trade.pnl > 0, 1), else_=0)).label("wins"),
            func.sum(case((Trade.pnl < 0, 1), else_=0)).label("losses"),
            func.sum(case((Trade.pnl == 0, 1), else_=0)).label("breakeven"),
            func.sum(Trade.pnl).label("day_pnl"),
            func.sum(case((Trade.pnl > 0, Trade.pnl), else_=0)).label("gross_profit"),
            func.sum(case((Trade.pnl < 0, func.abs(Trade.pnl)), else_=0)).label("gross_loss"),
            func.max(Trade.pnl).label("best"),
            func.min(Trade.pnl).label("worst"),
        )
        .group_by(_day_expression(db))
        .all()
    )
    daily_rows.sort(key=lambda row: row.day)
    if not daily_rows:
        return _empty_stats()

    trades_count = sum(int(row.trades_count or 0) for row in daily_rows)
    wins = sum(int(row.wins or 0) for row in daily_rows)
    losses = sum(int(row.losses or 0) for row in daily_rows)
    breakeven = sum(int(row.breakeven or 0) for row in daily_rows)
    net_pnl = sum((_money(row.day_pnl) for row in daily_rows), Decimal("0"))
    gross_profit = sum((_money(row.gross_profit) for row in daily_rows), Decimal("0"))
    gross_loss = sum((_money(row.gross_loss) for row in daily_rows), Decimal("0"))
    best_trade = max(_money(row.best) for row in daily_rows)
    worst_trade = min(_money(row.worst) for row in daily_rows)

    equity_curve: list[dict[str, str]] = []
    current_cum_pnl = Decimal("0")
    peak_pnl = Decimal("0")
    max_drawdown = Decimal("0")
    previous_day: date | None = None
    for row in daily_rows:
        day = row.day if isinstance(row.day, date) else date.fromisoformat(str(row.day))
        if previous_day is not None:
            day_cursor = previous_day + timedelta(days=1)
            while day_cursor < day:
                equity_curve.append(
                    {
                        "date": day_cursor.isoformat(),
                        "day_pnl": "0.00",
                        "cum_pnl": _format_money(current_cum_pnl),
                    }
                )
                day_cursor += timedelta(days=1)

        day_pnl = _money(row.day_pnl)
        current_cum_pnl += day_pnl
        peak_pnl = max(peak_pnl, current_cum_pnl)
        max_drawdown = max(max_drawdown, peak_pnl - current_cum_pnl)
        equity_curve.append(
            {
                "date": day.isoformat(),
                "day_pnl": _format_money(day_pnl),
                "cum_pnl": _format_money(current_cum_pnl),
            }
        )
        previous_day = day

    return {
        "trades_count": trades_count,
        "wins": wins,
        "losses": losses,
        "breakeven": breakeven,
        "net_pnl": _format_money(net_pnl),
        "gross_profit": _format_money(gross_profit),
        "gross_loss": _format_money(gross_loss),
        "win_rate": round(wins / trades_count, 4),
        "profit_factor": round(float(gross_profit / gross_loss), 4) if gross_loss else None,
        "avg_win": _format_money(gross_profit / wins) if wins else None,
        "avg_loss": _format_money(-gross_loss / losses) if losses else None,
        "best_trade": _format_money(best_trade),
        "worst_trade": _format_money(worst_trade),
        "max_drawdown": _format_money(max_drawdown),
        "equity_curve": equity_curve,
    }
