#!/bin/sh
set -eu

echo "[web] alembic upgrade head"
alembic upgrade head

echo "[web] start uvicorn"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
