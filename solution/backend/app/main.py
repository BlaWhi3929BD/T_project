from typing import List, Optional
from datetime import date
from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from app.database import create_db_and_tables, get_db
from app import crud, schemas

# Используем Lifespan для управления жизненным циклом приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Действия при запуске
    create_db_and_tables()
    yield
    # Действия при завершении (если нужны)

# Инициализация FastAPI приложения
app = FastAPI(
    title="Trades Dashboard API",
    description="API для дашборда аналитики по сделкам",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def read_root():
    """
    Корневой эндпоинт, возвращающий приветственное сообщение.
    """
    return {"message": "Welcome to the Trades Dashboard API!"}

@app.get("/api/filters/options", response_model=schemas.FilterOptions)
async def get_filters_options(db: Session = Depends(get_db)):
    """
    Возвращает список доступных символов и стратегий для фильтрации сделок.
    """
    symbols, strategies = crud.get_filter_options(db)
    return {"symbols": symbols, "strategies": strategies}

@app.get("/api/trades", response_model=schemas.TradeListResponse)
async def list_trades(
    db: Session = Depends(get_db),
    symbol: Optional[List[str]] = Query(None, description="Фильтр по символу"),
    strategy: Optional[List[str]] = Query(None, description="Фильтр по стратегии"),
    side: Optional[str] = Query(None, pattern="^(long|short)$", description="Фильтр по стороне сделки"),
    date_from: Optional[date] = Query(None, description="Фильтр по дате закрытия от"),
    date_to: Optional[date] = Query(None, description="Фильтр по дате закрытия до"),
    sort: str = Query("closed_at", pattern="^(closed_at|pnl|symbol)$", description="Поле для сортировки"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Порядок сортировки"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(50, ge=1, le=200, description="Размер страницы"),
):
    """
    Возвращает список торговых сделок с фильтрацией, сортировкой и пагинацией.
    """
    trades, total_trades = crud.get_trades(
        db=db,
        symbols=symbol,
        strategies=strategy,
        side=side,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort,
        order=order,
        page=page,
        page_size=page_size,
    )
    return {"items": trades, "page": page, "page_size": page_size, "total": total_trades}

@app.get("/api/stats", response_model=schemas.StatsResponse)
async def get_trades_stats(
    db: Session = Depends(get_db),
    symbol: Optional[List[str]] = Query(None, description="Фильтр по символу"),
    strategy: Optional[List[str]] = Query(None, description="Фильтр по стратегии"),
    side: Optional[str] = Query(None, pattern="^(long|short)$", description="Фильтр по стороне сделки"),
    date_from: Optional[date] = Query(None, description="Фильтр по дате закрытия от"),
    date_to: Optional[date] = Query(None, description="Фильтр по дате закрытия до"),
):
    """
    Возвращает статистические данные по отфильтрованным сделкам.
    """
    stats = crud.get_trade_stats(
        db=db,
        symbols=symbol,
        strategies=strategy,
        side=side,
        date_from=date_from,
        date_to=date_to,
    )
    return stats
