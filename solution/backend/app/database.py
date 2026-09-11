import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Получаем абсолютный путь к директории проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Определяем путь к файлу SQLite базы данных внутри директории `solution/backend`
SQLITE_FILE_NAME = "trades.db"
DEFAULT_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, SQLITE_FILE_NAME)}"

# Читаем URL базы данных из переменной окружения DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

# Создаем SQLAlchemy engine с учетом типа базы данных
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Оптимизации для пула соединений PostgreSQL
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(DATABASE_URL, **engine_kwargs)

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
