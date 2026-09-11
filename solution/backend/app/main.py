import logging
from contextlib import asynccontextmanager
from datetime import date

from app import crud, schemas
from app.database import create_db_and_tables, get_db
from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


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
    lifespan=lifespan,
)


@app.get("/")
def read_root():
    """
    Корневой эндпоинт, возвращающий приветственное сообщение.
    """
    return {"message": "Welcome to the Trades Dashboard API!"}


@app.get("/health", status_code=200)
def health():
    """
    Эндпоинт проверки жизнеспособности (liveness probe).
    Возвращает 200 {"status":"ok"}, к базе данных не обращается.
    """
    return {"status": "ok"}


@app.get("/ready", status_code=200)
def ready(db: Session = Depends(get_db)):
    """
    Эндпоинт проверки готовности (readiness probe).
    Проверяет доступность базы данных через SELECT 1.
    Возвращает 200 при успехе, иначе 503 Service Unavailable.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.exception("Database readiness check failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unreachable",
        ) from e


@app.get("/api/filters/options", response_model=schemas.FilterOptions)
def get_filters_options(db: Session = Depends(get_db)):
    """
    Возвращает список доступных символов и стратегий для фильтрации сделок.
    """
    symbols, strategies = crud.get_filter_options(db)
    return {"symbols": symbols, "strategies": strategies}


@app.get("/api/trades", response_model=schemas.TradeListResponse)
def list_trades(
    db: Session = Depends(get_db),
    symbol: list[str] | None = Query(
        None, max_length=crud.MAX_FILTER_VALUES, description="Фильтр по символу"
    ),
    strategy: list[str] | None = Query(
        None, max_length=crud.MAX_FILTER_VALUES, description="Фильтр по стратегии"
    ),
    side: str | None = Query(
        None, pattern="^(long|short)$", description="Фильтр по стороне сделки"
    ),
    date_from: date | None = Query(None, description="Фильтр по дате закрытия от"),
    date_to: date | None = Query(None, description="Фильтр по дате закрытия до"),
    sort: str = Query(
        "closed_at", pattern="^(closed_at|pnl|symbol)$", description="Поле для сортировки"
    ),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Порядок сортировки"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(50, ge=1, le=200, description="Размер страницы"),
):
    """
    Возвращает список торговых сделок с фильтрацией, сортировкой и пагинацией.
    """
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must not be after date_to")

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
def get_trades_stats(
    db: Session = Depends(get_db),
    symbol: list[str] | None = Query(
        None, max_length=crud.MAX_FILTER_VALUES, description="Фильтр по символу"
    ),
    strategy: list[str] | None = Query(
        None, max_length=crud.MAX_FILTER_VALUES, description="Фильтр по стратегии"
    ),
    side: str | None = Query(
        None, pattern="^(long|short)$", description="Фильтр по стороне сделки"
    ),
    date_from: date | None = Query(None, description="Фильтр по дате закрытия от"),
    date_to: date | None = Query(None, description="Фильтр по дате закрытия до"),
):
    """
    Возвращает статистические данные по отфильтрованным сделкам.
    """
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must not be after date_to")

    stats = crud.get_trade_stats(
        db=db,
        symbols=symbol,
        strategies=strategy,
        side=side,
        date_from=date_from,
        date_to=date_to,
    )
    return stats
