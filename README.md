# Дашборд аналитики по сделкам

Это одностраничное приложение для визуализации и анализа торговых сделок. Проект включает в себя API на FastAPI и интерактивный дашборд на React.

## Структура проекта

- `backend/`: FastAPI API, работа с БД (SQLite), логика агрегации и тесты.
- `frontend/`: React-приложение (TypeScript, Vite).
- `task/`: Исходные данные (`trades.csv`) и скрипт генерации (`seed.py`).

## Бэкенд

### Настройка и запуск
1. Перейти в директорию и создать виртуальное окружение:
   ```bash
   cd backend && python3 -m venv .venv
   # Активация: source .venv/bin/activate (Bash) или source .venv/bin/activate.fish (Fish)
   ```
2. Установить зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Загрузить данные из CSV в SQLite:
   ```bash
   python3 scripts/seed_db.py
   ```
4. Запустить API:
   ```bash
   PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
API доступно по адресу `http://localhost:8000`, документация Swagger — `http://localhost:8000/docs`.

## Фронтенд

### Запуск
1. Перейти в директорию: `cd frontend`
2. Установить зависимости: `npm install`
3. Запустить сервер разработки: `npm run dev`
Фронтенд будет доступен по адресу `http://localhost:3000`.

## Тестирование
Для запуска автотестов на бэкенде:
```bash
cd backend && pytest tests/
```

## Замеры производительности
Для оценки скорости работы API (p95 < 200мс для `/api/stats`, p95 < 100мс для `/api/trades`) используйте `ab` (Apache Benchmark):
```bash
ab -n 100 -c 10 http://localhost:8000/api/stats
ab -n 100 -c 10 http://localhost:8000/api/trades
```
Результаты замеров должны быть добавлены в `DECISIONS.md`.

## Дополнительная документация
Подробное обоснование всех принятых технических решений находится в файле `DECISIONS.md`.
