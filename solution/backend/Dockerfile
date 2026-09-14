FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 10001 appgroup \
    && useradd --uid 10001 --gid appgroup --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/task/data \
    && chown appuser:appgroup /app \
    && chown -R appuser:appgroup /app/task

COPY solution/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY solution/backend/app ./app
COPY solution/backend/scripts ./scripts
COPY --chown=appuser:appgroup solution/backend/entrypoint.sh ./entrypoint.sh
COPY --chown=appuser:appgroup task/data/seed.py ./task/data/seed.py

ENTRYPOINT ["/app/entrypoint.sh"]

FROM runtime AS test

COPY solution/backend/tests ./tests
RUN pip install --no-cache-dir pytest httpx
USER appuser
CMD ["pytest", "-q", "tests"]

FROM runtime AS final

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10m --retries=3 \
    CMD curl --fail --silent http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
