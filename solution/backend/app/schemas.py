from datetime import datetime
from typing import List, Optional, Annotated
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from decimal import Decimal

# Валидатор для автоматической конвертации Decimal в строку (требование задания)
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
    items: List[Trade]
    page: int
    page_size: int
    total: int

class FilterOptions(BaseModel):
    symbols: List[str]
    strategies: List[str]

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
    win_rate: Optional[float]
    profit_factor: Optional[float]
    avg_win: Optional[str]
    avg_loss: Optional[str]
    best_trade: str
    worst_trade: str
    max_drawdown: str
    equity_curve: List[EquityCurvePoint]
