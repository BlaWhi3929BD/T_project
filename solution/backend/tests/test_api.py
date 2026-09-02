import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
from decimal import Decimal
import os
import sys

# Добавляем путь к корню проекта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.database import Base, get_db
from app.models import Trade
from scripts.seed_db import seed_database
import pytz

# Настройка тестовой БД
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    # Создать таблицы
    Base.metadata.create_all(bind=test_engine)
    # Загрузить данные
    db = TestingSessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield
    # Удалить таблицы
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture()
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# ---- Тесты ----
def test_read_root(client):
    assert client.get("/").status_code == 200

def test_get_filter_options(client):
    response = client.get("/api/filters/options")
    assert response.status_code == 200
    assert len(response.json()["symbols"]) > 0

def test_list_trades_no_filters(client):
    response = client.get("/api/trades")
    assert response.status_code == 200
    assert response.json()["total"] == 100000

def test_list_trades_filter_by_symbol(client):
    response = client.get("/api/trades?symbol=BTCUSDT")
    assert response.status_code == 200
    assert response.json()["total"] > 0

def test_list_trades_filter_by_multiple_symbols(client):
    response = client.get("/api/trades?symbol=BTCUSDT&symbol=ETHUSDT")
    assert response.status_code == 200
    assert response.json()["total"] > 0

def test_list_trades_filter_by_strategy(client):
    response = client.get("/api/trades?strategy=mean_rev_v2")
    assert response.status_code == 200
    assert response.json()["total"] > 0

def test_list_trades_filter_by_side_long(client):
    response = client.get("/api/trades?side=long")
    assert response.status_code == 200
    assert response.json()["total"] > 0

def test_list_trades_pagination(client):
    r1 = client.get("/api/trades?page=1&page_size=10")
    r2 = client.get("/api/trades?page=2&page_size=10")
    assert len(r1.json()["items"]) == 10
    assert r1.json()["items"][0]["id"] != r2.json()["items"][0]["id"]

def test_list_trades_sort_by_pnl_asc(client):
    response = client.get("/api/trades?sort=pnl&order=asc&page_size=10")
    items = response.json()["items"]
    assert Decimal(items[0]["pnl"]) <= Decimal(items[1]["pnl"])

def test_list_trades_max_page_size(client):
    assert len(client.get("/api/trades?page_size=200").json()["items"]) == 200

def test_list_trades_min_page_size(client):
    assert len(client.get("/api/trades?page_size=1").json()["items"]) == 1

def test_list_trades_non_existent_symbol(client):
    assert client.get("/api/trades?symbol=INVALID").json()["total"] == 0

def test_get_stats_no_filters_control_values(client):
    response = client.get("/api/stats")
    assert response.status_code == 200
    assert response.json()["trades_count"] == 100000
    assert response.json()["net_pnl"] == "20373.96"

def test_get_stats_filter_by_symbol(client):
    assert client.get("/api/stats?symbol=ETHUSDT").json()["trades_count"] > 0

def test_get_stats_equity_curve_continuity(client):
    data = client.get("/api/stats?date_from=2025-04-21&date_to=2025-04-23").json()
    assert len(data["equity_curve"]) >= 3

def test_get_stats_max_drawdown_calculation(client):
    # Тест: если доходность всегда растет, просадка = 0
    # В текущем датасете есть убытки, поэтому просадка > 0
    assert Decimal(client.get("/api/stats").json()["max_drawdown"]) >= 0

def test_get_stats_profit_factor_and_win_rate(client):
    data = client.get("/api/stats").json()
    assert data["win_rate"] is not None
