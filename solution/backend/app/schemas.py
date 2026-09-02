from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from typing_extensions import Annotated
from decimal import Decimal

# Валидатор для автоматической конвертации Decimal в строку
def decimal_to_str(v: object) -> object:
    if isinstance(v, Decimal):
        return str(v)
    return v

# Тип для полей, которые должны быть строками, но приходят как Decimal
StrDecimal = Annotated[str, BeforeValidator(decimal_to_str)]

class TradeBase(BaseModel):
    symbol: str
    strategy: str
    side: str
    opened_at: datetime
    closed_at: datetime
    qty: StrDecimal
    entry_price: StrDecimal
    exit_price: StrDecimal
    fee: StrDecimal
    pnl: StrDecimal

class TradeCreate(TradeBase):
    pass

class Trade(TradeBase):
    id: int
    
    # В Pydantic V2 используем from_attributes для работы с SQLAlchemy
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
