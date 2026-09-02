# Иерархия проекта

Этот документ описывает структуру файлов и папок проекта.

## Структура

```text
solution/
├── backend/                # Серверная часть (FastAPI)
│   ├── app/                # Основное приложение
│   │   ├── main.py         # Эндпоинты API
│   │   ├── database.py     # Конфигурация БД (SQLite)
│   │   ├── models.py       # SQL-модели (SQLAlchemy)
│   │   ├── schemas.py      # Pydantic-схемы (типы API)
│   │   └── crud.py         # Бизнес-логика и запросы к БД
│   ├── scripts/            # Вспомогательные скрипты
│   │   └── seed_db.py      # Загрузка CSV в БД
│   ├── tests/              # Тесты
│   │   └── test_api.py     # Тесты эндпоинтов
│   └── requirements.txt    # Зависимости Python
│
├── frontend/               # Клиентская часть (React + Vite)
│   ├── src/                # Исходный код
│   │   ├── components/     # UI-компоненты
│   │   ├── hooks/          # Логика состояния
│   │   ├── services/       # API-сервисы
│   │   └── types/          # TypeScript-типы
│   ├── index.html          # Точка входа HTML
│   ├── package.json        # Зависимости JS
│   ├── tsconfig.json       # Конфигурация TypeScript
│   └── vite.config.ts      # Конфигурация Vite
│
├── README.md               # Инструкции по запуску
└── DECISIONS.md            # Журнал технических решений
```
