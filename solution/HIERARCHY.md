# Иерархия проекта

Этот документ описывает актуальную структуру файлов и папок проекта с учетом инфраструктуры Docker Compose и Kubernetes.

## Структура

```text
/
├── docker-compose.yml          # Оркестрация сервисов (PostgreSQL, Backend, Frontend, Seed Job)
├── .env.example                # Плейсхолдеры секретов и переменных окружения
├── requirements.txt            # Зависимости Python в корне
├── README.md                   # Руководство по запуску и деплою
│
├── k8s/                        # Манифесты Kubernetes (Kustomize)
│   ├── namespace.yaml          # Изолированный namespace trades-dashboard
│   ├── postgres-secret.yaml    # Секрет с учетными данными БД
│   ├── postgres.yaml           # StatefulSet и headless Service для PostgreSQL
│   ├── configmap.yaml          # ConfigMap с несекретными настройками
│   ├── backend.yaml            # Deployment и Service бэкенда с securityContext
│   ├── frontend.yaml           # Deployment и Service фронтенда (Nginx)
│   ├── db-seed-job.yaml        # Job однократного импорта данных из CSV
│   ├── ingress.yaml            # Ingress правила (trades.local)
│   └── kustomization.yaml      # Конфигурация Kustomize
│
└── solution/
    ├── backend/                # Серверная часть (FastAPI)
    │   ├── app/                # Основное приложение
    │   │   ├── main.py         # Эндпоинты API (/health, /ready, /api/...)
    │   │   ├── database.py     # Конфигурация БД (PostgreSQL / SQLite)
    │   │   ├── models.py       # SQL-модели (SQLAlchemy, Numeric, DateTime)
    │   │   ├── schemas.py      # Pydantic-схемы (типы API)
    │   │   └── crud.py         # Бизнес-логика, агрегаты, Pandas
    │   ├── scripts/            # Вспомогательные скрипты
    │   │   └── seed_db.py      # Пакетная загрузка CSV в БД (--if-empty)
    │   ├── tests/              # Автотесты
    │   │   └── test_api.py     # 19 тестов pytest
    │   ├── Dockerfile          # Multi-stage Dockerfile бэкенда (с тестами)
    │   └── requirements.txt    # Зависимости Python для сборки образа
    │
    ├── frontend/               # Клиентская часть (React + Vite)
    │   ├── src/                # Исходный код
    │   │   ├── components/     # UI-компоненты (Metrics, Charts, Table, Filters)
    │   │   ├── hooks/          # Логика состояния (useDashboardFilters)
    │   │   ├── services/       # API-сервисы
    │   │   └── types/          # TypeScript-типы
    │   ├── Dockerfile          # Multi-stage Dockerfile фронтенда (Nginx)
    │   ├── nginx.conf          # Конфигурация Nginx и реверс-прокси
    │   ├── index.html          # Точка входа HTML
    │   ├── package.json        # Зависимости JS
    │   ├── tsconfig.json       # Конфигурация TypeScript
    │   └── vite.config.ts      # Конфигурация Vite
    │
    ├── HIERARCHY.md            # Структура файлов проекта
    └── DECISIONS.md            # Журнал технических решений (9 записей)
```
