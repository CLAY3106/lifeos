#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Seeding demo account (idempotent)..."
python -m app.seed

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
