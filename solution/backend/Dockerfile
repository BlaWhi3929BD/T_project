FROM python:3.11-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# curl is installed from the pinned Debian base image; the package version
# varies between security rebuilds of that image.
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 10001 appgroup \
    && useradd --uid 10001 --gid appgroup --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/task/data \
    && chown appuser:appgroup /app \
    && chown -R appuser:appgroup /app/task

COPY solution/backend/requirements.txt ./requirements.txt
# requirements.txt pins every runtime dependency.
# hadolint ignore=DL3013
RUN pip install --no-cache-dir -r requirements.txt

COPY solution/backend/app ./app
COPY solution/backend/scripts ./scripts
COPY --chown=appuser:appgroup solution/backend/entrypoint.sh ./entrypoint.sh
COPY --chown=appuser:appgroup task/data/seed.py ./task/data/seed.py

ENTRYPOINT ["/app/entrypoint.sh"]

FROM runtime AS test

COPY solution/backend/tests ./tests
COPY solution/backend/test-requirements.txt ./test-requirements.txt
RUN pip install --no-cache-dir -r test-requirements.txt
USER appuser
CMD ["pytest", "-q", "tests"]

FROM runtime AS final

RUN pip uninstall --yes pip wheel jaraco.context
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10m --retries=3 \
    CMD curl --fail --silent http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
