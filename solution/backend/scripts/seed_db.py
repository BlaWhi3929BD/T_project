
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

def seed_database(db: Session, force: bool = True, csv_path: str = None):
    """
    Загружает данные из trades.csv в базу данных (SQLite или PostgreSQL).
    
    Args:
        db (Session): Сессия базы данных SQLAlchemy.
        force (bool): Если False и в таблице уже есть записи, сидинг пропускается.
        csv_path (str): Опциональный путь к CSV файлу.
    """
    create_db_and_tables()

    current_count = db.query(Trade).count()
    if not force and current_count > 0:
        print(f"Таблица trades уже содержит {current_count} записей. Пропуск сидинга.")
        return

    if force and current_count > 0:
        print("Удаление существующих данных...")
        db.query(Trade).delete()
        db.commit()

    if not csv_path:
        # Проверяем возможные пути: относительно скрипта или через переменную окружения
        env_csv = os.getenv("CSV_PATH")
        if env_csv and os.path.exists(env_csv):
            csv_path = env_csv
        else:
            default_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'task', 'data', 'trades.csv'))
            if os.path.exists(default_path):
                csv_path = default_path
            else:
                csv_path = os.path.abspath("task/data/trades.csv")

    print(f"Чтение данных из {csv_path}...")
    df = pd.read_csv(csv_path)

    df['opened_at'] = pd.to_datetime(df['opened_at'], utc=True)
    df['closed_at'] = pd.to_datetime(df['closed_at'], utc=True)
    for col in ['qty', 'entry_price', 'exit_price', 'fee', 'pnl']:
        df[col] = df[col].apply(Decimal)

    print(f"Загрузка {len(df)} сделок через bulk_insert_mappings...")
    records = df.to_dict(orient='records')
    
    # Пакетная вставка для высокой производительности как в SQLite, так и в PostgreSQL
    batch_size = 10000
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        db.bulk_insert_mappings(Trade, batch)
        db.commit()
        print(f"Загружено {min(i + batch_size, len(records))} / {len(records)} записей...")

    print("Данные успешно загружены.")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        # При прямом запуске скрипта поддерживаем аргумент --if-empty для безопасного перезапуска
        force_seed = "--if-empty" not in sys.argv
        seed_database(db, force=force_seed)
    finally:
        db.close()

