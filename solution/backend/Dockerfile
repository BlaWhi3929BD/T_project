# Базовый образ с оптимизированными параметрами Python
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Установка минимальных системных зависимостей для cURL (HEALTHCHECK)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание непривилегированного пользователя (Non-root)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh appuser

# Установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода бэкенда и скриптов
COPY app ./app
COPY scripts ./scripts

RUN chown -R appuser:appgroup /app

# Стадия тестирования: запуск pytest внутри контейнера (docker build --target test .)
FROM base AS test
COPY tests ./tests
# Установка pytest для прогона тестов
RUN pip install --no-cache-dir pytest httpx
USER appuser
CMD ["pytest", "tests/"]

# Финальная стадия для Production
FROM base AS final
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
