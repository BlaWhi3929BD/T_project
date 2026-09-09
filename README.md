# Дашборд аналитики по сделкам

Это одностраничное приложение для визуализации и анализа торговых сделок. Включает в себя API на FastAPI, интерактивный дашборд на React и поддержку развёртывания через Docker Compose и Kubernetes.

## Структура

- `solution/backend/`: FastAPI API, работа с БД (PostgreSQL / SQLite), логика агрегации и тесты.
- `solution/frontend/`: React-приложение (TypeScript, Vite, Nginx).
- `docker-compose.yml`: Конфигурация Docker Compose для локального запуска.
- `task/`: Исходные данные (`trades.csv`) и скрипт генерации (`seed.py`).
- `solution/DECISIONS.md`: Журнал технических решений.

---

## 1. Локальный запуск (без Docker)

### Бэкенд

#### Настройка:
```bash
# 0. Клонировать репозиторий:
git clone -b feature/trades-dashboard --single-branch https://github.com/BlaWhi3929BD/T_project.git

cd T_project

# 1. Создать виртуальное окружение:
# Bash / Linux / macOS:
python3 -m venv .venv

# Windows (PowerShell):
# python -m venv .venv

# 2. Активация:
# Bash:
source .venv/bin/activate

# Fish:
# source .venv/bin/activate.fish

# Windows (PowerShell):
# .venv\Scripts\Activate.ps1

# Windows (CMD):
# .venv\Scripts\activate.bat

# 3. Установить зависимости:
pip install -r requirements.txt

# 4. Загрузить данные из CSV в SQLite:
python solution/backend/scripts/seed_db.py
```

#### Запуск:
```bash
# Bash:
PYTHONPATH=solution/backend .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000

# Fish:
# env PYTHONPATH=solution/backend .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000

# Windows (PowerShell / CMD):
# set PYTHONPATH=solution/backend
# venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```
API доступно по адресу `http://localhost:8000`. Документация Swagger — `http://localhost:8000/docs`.

### Фронтенд

#### Запуск:
```bash
cd solution/frontend

# Установить зависимости:
npm install

# Запустить сервер разработки:
npm run dev
```
Фронтенд будет доступен по адресу `http://localhost:3000` (с проксированием `/api` на бэкенд).

---

## 2. Развёртывание через Docker Compose (Рекомендуется)

### Предварительные требования
Установленные **Docker** и **Docker Compose (v2+)**.

### Первый запуск (с нуля)
1. Скопируйте файл с переменными окружения:
   ```bash
   cp .env.example .env
   ```
   *(При необходимости отредактируйте параметры БД в `.env`)*

2. Запустите сборку и развёртывание одной командой:
   ```bash
   docker compose up --build -d
   ```
   *Что происходит при первом запуске:* поднимается PostgreSQL 16, сервис `db-seed` один раз импортирует 100 000 строк из `trades.csv` в БД, после чего стартуют бэкенд и фронтенд.

### Проверка работоспособности
- **Дашборд:** открыть в браузере `http://localhost:8080` (графики и таблица должны быть заполнены данными).
- **Метрики API:** `curl http://localhost:8080/api/stats` (отдаёт JSON).
- **Эндпоинты здоровья:**
  - `curl http://localhost:8080/health` → `200 {"status":"ok"}`
  - `curl http://localhost:8080/ready` → `200 {"status":"ready"}`
- **Безопасность портов:** `curl http://localhost:8000` с хоста **не отвечает** (порт бэкенда изолирован внутри сети Docker).
- **Статус контейнеров:** `docker compose ps` — все три сервиса (`trades-postgres`, `trades-backend`, `trades-frontend`) должны быть в состоянии `healthy` (trades-frontend иногда может быть unhealthy).

### Повторный запуск (без пересоздания и без повторного сидинга)
Если вы остановили контейнеры через `docker compose down`:
```bash
docker compose up -d
```
*Данные в PostgreSQL сохраняются в именованном томе (`postgres_data`). Повторная загрузка CSV не производится, время старта минимально.*

### Запуск тестов в контейнере
Для запуска всех тестов `pytest` внутри изолированного контейнера бэкенда:
```bash
docker build --target test -t trades-backend-test -f solution/backend/Dockerfile solution/backend
docker run --rm -v $(pwd)/task/data:/app/task/data trades-backend-test
```
*(Либо через Docker Compose):*

```bash
docker compose run --rm backend-test
```

### Полный сброс (удаление данных и контейнеров)

Для полного уничтожения окружения вместе с базой данных и томами:

```bash
docker compose down -v
```

---

## Тестирование локально (без Docker)

Для запуска автотестов на бэкенде:

```bash
.venv/bin/pytest solution/backend/tests/

```

```

```

## Дополнительная документация
Подробное обоснование всех принятых технических решений находится в файле `solution/DECISIONS.md`.
