#!/bin/sh
set -eu

csv_path="${CSV_PATH:-/app/task/data/trades.csv}"
if [ ! -f "$csv_path" ]; then
    python task/data/seed.py
fi

python -m app.seed --if-empty
exec "$@"
