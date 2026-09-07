
import os
import pandas as pd
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

# Изменяем PYTHONPATH, чтобы скрипт мог импортировать модули из `app`
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine, Base, SessionLocal, create_db_and_tables
from app.models import Trade

def seed_database(db: Session):
    """
    Загружает данные из trades.csv в базу данных SQLite.
    Предварительно удаляет все существующие записи в таблице trades.

    Args:
        db (Session): Сессия базы данных SQLAlchemy.
    """
    print("Создание таблиц базы данных...")
    create_db_and_tables() # Убедимся, что таблицы созданы

    print("Удаление существующих данных...")
    db.query(Trade).delete()
    db.commit()

    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'task', 'data', 'trades.csv'))
    print(f"Чтение данных из {csv_path}...")
    df = pd.read_csv(csv_path)

    # Преобразование типов данных
    df['opened_at'] = pd.to_datetime(df['opened_at'], utc=True)
    df['closed_at'] = pd.to_datetime(df['closed_at'], utc=True)
    for col in ['qty', 'entry_price', 'exit_price', 'fee', 'pnl']:
        df[col] = df[col].apply(Decimal)

    print(f"Загрузка {len(df)} сделок в базу данных...")
    for index, row in df.iterrows():
        trade = Trade(
            id=row['id'],
            symbol=row['symbol'],
            strategy=row['strategy'],
            side=row['side'],
            opened_at=row['opened_at'],
            closed_at=row['closed_at'],
            qty=row['qty'],
            entry_price=row['entry_price'],
            exit_price=row['exit_price'],
            fee=row['fee'],
            pnl=row['pnl']
        )
        db.add(trade)
        if (index + 1) % 1000 == 0: # Коммитим каждые 1000 записей для оптимизации памяти
            db.commit()
            print(f"Загружено {index + 1} записей...")
    db.commit() # Коммит оставшихся записей
    print("Данные успешно загружены.")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
