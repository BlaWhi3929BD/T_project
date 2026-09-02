from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, case
from app.models import Trade
from app.schemas import TradeCreate
import pytz
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

ALMATY_TZ = pytz.timezone('Asia/Almaty')

def create_trade(db: Session, trade: TradeCreate):
    db_trade = Trade(
        symbol=trade.symbol, strategy=trade.strategy, side=trade.side,
        opened_at=trade.opened_at, closed_at=trade.closed_at,
        qty=Decimal(trade.qty), entry_price=Decimal(trade.entry_price),
        exit_price=Decimal(trade.exit_price), fee=Decimal(trade.fee), pnl=Decimal(trade.pnl)
    )
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade

def get_trades(db: Session, symbols=None, strategies=None, side=None, date_from=None, date_to=None, sort_by="closed_at", order="desc", page=1, page_size=50):
    query = db.query(Trade)
    if symbols: query = query.filter(Trade.symbol.in_(symbols))
    if strategies: query = query.filter(Trade.strategy.in_(strategies))
    if side: query = query.filter(Trade.side == side)
    
    if date_from:
        dt_from_utc = ALMATY_TZ.localize(datetime(date_from.year, date_from.month, date_from.day, 0, 0, 0)).astimezone(pytz.utc)
        query = query.filter(Trade.closed_at >= dt_from_utc)
    if date_to:
        dt_to_utc = ALMATY_TZ.localize(datetime(date_to.year, date_to.month, date_to.day, 23, 59, 59, 999999)).astimezone(pytz.utc)
        query = query.filter(Trade.closed_at <= dt_to_utc)

    total_trades = query.count()
    sort_column = getattr(Trade, sort_by, Trade.closed_at)
    
    if order == "asc":
        query = query.order_by(asc(sort_column), asc(Trade.id))
    else:
        query = query.order_by(desc(sort_column), asc(Trade.id))
    
    trades = query.offset((page - 1) * page_size).limit(page_size).all()
    return trades, total_trades

def get_filter_options(db: Session) -> Tuple[List[str], List[str]]:
    symbols = [s[0] for s in db.query(Trade.symbol).distinct().order_by(Trade.symbol).all()]
    strategies = [s[0] for s in db.query(Trade.strategy).distinct().order_by(Trade.strategy).all()]
    return symbols, strategies

def get_trade_stats(db: Session, symbols=None, strategies=None, side=None, date_from=None, date_to=None) -> Dict[str, Any]:
    query = db.query(Trade)
    if symbols: query = query.filter(Trade.symbol.in_(symbols))
    if strategies: query = query.filter(Trade.strategy.in_(strategies))
    if side: query = query.filter(Trade.side == side)
    if date_from:
        dt_from_utc = ALMATY_TZ.localize(datetime(date_from.year, date_from.month, date_from.day, 0, 0, 0)).astimezone(pytz.utc)
        query = query.filter(Trade.closed_at >= dt_from_utc)
    if date_to:
        dt_to_utc = ALMATY_TZ.localize(datetime(date_to.year, date_to.month, date_to.day, 23, 59, 59, 999999)).astimezone(pytz.utc)
        query = query.filter(Trade.closed_at <= dt_to_utc)

    # 1. SQL Агрегация
    stats = query.with_entities(
        func.count(Trade.id),
        func.sum(case((Trade.pnl > 0, 1), else_=0)),
        func.sum(case((Trade.pnl < 0, 1), else_=0)),
        func.sum(case((Trade.pnl == 0, 1), else_=0)),
        func.sum(Trade.pnl),
        func.sum(case((Trade.pnl > 0, Trade.pnl), else_=0)),
        func.sum(case((Trade.pnl < 0, func.abs(Trade.pnl)), else_=0)),
        func.max(Trade.pnl),
        func.min(Trade.pnl)
    ).first()

    trades_count, wins, losses, breakeven, net_pnl, gross_profit, gross_loss, best, worst = stats
    if not trades_count:
        return {
            "trades_count": 0, "wins": 0, "losses": 0, "breakeven": 0,
            "net_pnl": "0.00", "gross_profit": "0.00", "gross_loss": "0.00",
            "win_rate": None, "profit_factor": None, "avg_win": None, "avg_loss": None,
            "best_trade": "0.00", "worst_trade": "0.00", "max_drawdown": "0.00", "equity_curve": []
        }

    # 2. Pandas для Equity Curve (очень быстро)
    trades_raw = query.with_entities(Trade.pnl, Trade.closed_at).all()
    df = pd.DataFrame(trades_raw, columns=['pnl', 'closed_at'])
    df['closed_at'] = pd.to_datetime(df['closed_at']).dt.tz_localize('UTC').dt.tz_convert('Asia/Almaty')
    df['date'] = df['closed_at'].dt.date
    
    daily = df.groupby('date')['pnl'].apply(lambda x: x.apply(Decimal).sum()).sort_index()
    full_range = pd.date_range(start=daily.index.min(), end=daily.index.max(), freq='D').date
    daily = daily.reindex(full_range, fill_value=Decimal('0.00'))

    equity_curve_data = []
    current_cum_pnl = Decimal('0.00')
    peak_pnl = Decimal('0.00')
    max_drawdown = Decimal('0.00')

    for day, pnl in daily.items():
        current_cum_pnl += pnl
        if current_cum_pnl > peak_pnl: peak_pnl = current_cum_pnl
        drawdown = peak_pnl - current_cum_pnl
        if drawdown > max_drawdown: max_drawdown = drawdown
            
        equity_curve_data.append({
            "date": day.isoformat(),
            "day_pnl": str(pnl.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            "cum_pnl": str(current_cum_pnl.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        })

    return {
        "trades_count": trades_count,
        "wins": int(wins or 0), "losses": int(losses or 0), "breakeven": int(breakeven or 0),
        "net_pnl": str(Decimal(str(net_pnl or 0)).quantize(Decimal('0.01'), ROUND_HALF_UP)),
        "gross_profit": str(Decimal(str(gross_profit or 0)).quantize(Decimal('0.01'), ROUND_HALF_UP)),
        "gross_loss": str(Decimal(str(gross_loss or 0)).quantize(Decimal('0.01'), ROUND_HALF_UP)),
        "win_rate": round(wins / trades_count, 4),
        "profit_factor": round(float(gross_profit) / float(gross_loss), 4) if gross_loss and gross_loss > 0 else None,
        "avg_win": str((Decimal(str(gross_profit)) / wins).quantize(Decimal('0.01'), ROUND_HALF_UP)) if wins else None,
        "avg_loss": str(((-Decimal(str(gross_loss))) / losses).quantize(Decimal('0.01'), ROUND_HALF_UP)) if losses else None,
        "best_trade": str(Decimal(str(best)).quantize(Decimal('0.01'), ROUND_HALF_UP)),
        "worst_trade": str(Decimal(str(worst)).quantize(Decimal('0.01'), ROUND_HALF_UP)),
        "max_drawdown": str(max_drawdown.quantize(Decimal('0.01'), ROUND_HALF_UP)),
        "equity_curve": equity_curve_data
    }
