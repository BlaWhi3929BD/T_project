import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Получаем абсолютный путь к директории проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Определяем путь к файлу SQLite базы данных внутри директории `solution/backend`
SQLITE_FILE_NAME = "trades.db"
SQLITE_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, SQLITE_FILE_NAME)}"

# Создаем SQLAlchemy engine
# connect_args={"check_same_thread": False} необходимо для SQLite в FastAPI,
# так как SQLite по умолчанию позволяет только одному потоку взаимодействовать с базой данных.
engine = create_engine(
    SQLITE_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Создаем класс сессии базы данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для объявления моделей SQLAlchemy
Base = declarative_base()

# Зависимость для получения сессии базы данных
def get_db():
    """
    Предоставляет сессию базы данных для обработки запросов FastAPI.
    Гарантирует, что сессия будет закрыта после завершения запроса.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_db_and_tables():
    """
    Создает все таблицы в базе данных, определенные через Base.metadata.
    """
    Base.metadata.create_all(bind=engine)
