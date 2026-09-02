# Дашборд аналитики по сделкам

Это одностраничное приложение для визуализации и анализа торговых сделок. Включает в себя API на FastAPI и интерактивный дашборд на React.

## Структура

- `solution/backend/`: FastAPI API, работа с БД (SQLite), логика агрегации и тесты.
- `solution/frontend/`: React-приложение (TypeScript, Vite).
- `task/`: Исходные данные (`trades.csv`) и скрипт генерации (`seed.py`).

## Бэкенд

### Настройка
```bash
  # 1. Создать виртуальное окружение:
   python3 -m venv .venv
   
   # 2. Активация
   # Bash:
   source .venv/bin/activate
   
   # Fish:
   # source .venv/bin/activate.fish
   
   # 3. Установить зависимости:
   pip install -r requirements.txt
   
   # 4. Загрузить данные из CSV в SQLite:
   python3 solution/backend/scripts/seed_db.py
   ```
### Запуск:
   ```bash
   # Bash:
   PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 8000

   # Fish:
   # env PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 8000
   
   ```
API доступно по адресу `http://localhost:8000`.
Документация Swagger — `http://localhost:8000/docs`.

## Фронтенд

### Запуск
```bash
  # 1. Перейти в директорию:
  cd solution/frontend
  # 2. Установить зависимости:
  npm install
  # 3. Запустить сервер разработки:
  npm run dev
```
Фронтенд будет доступен по адресу `http://localhost:3000`.

## Тестирование
Для запуска автотестов на бэкенде:
```bash
  # Bash:
  source .venv/bin/activate
  
  # Fish:
  # source .venv/bin/activate.fish
  
  cd solution/backend && pytest tests/
```


## Дополнительная документация
Подробное обоснование всех принятых технических решений находится в файле `solution/DECISIONS.md`.
