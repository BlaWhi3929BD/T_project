from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict


def decimal_to_str(v: object) -> object:
    return str(v) if isinstance(v, Decimal) else v


StrField = Annotated[str, BeforeValidator(decimal_to_str)]


class TradeBase(BaseModel):
    symbol: str
    strategy: str
    side: str
    opened_at: datetime
    closed_at: datetime
    qty: StrField
    entry_price: StrField
    exit_price: StrField
    fee: StrField
    pnl: StrField


class TradeCreate(TradeBase):
    pass


class Trade(TradeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class TradeListResponse(BaseModel):
    items: list[Trade]
    page: int
    page_size: int
    total: int


class FilterOptions(BaseModel):
    symbols: list[str]
    strategies: list[str]


class EquityCurvePoint(BaseModel):
    date: str
    day_pnl: str
    cum_pnl: str


class StatsResponse(BaseModel):
    trades_count: int
    wins: int
    losses: int
    breakeven: int
    net_pnl: str
    gross_profit: str
    gross_loss: str
    win_rate: float | None
    profit_factor: float | None
    avg_win: str | None
    avg_loss: str | None
    best_trade: str
    worst_trade: str
    max_drawdown: str
    equity_curve: list[EquityCurvePoint]
