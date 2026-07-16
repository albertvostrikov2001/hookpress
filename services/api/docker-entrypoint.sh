#!/bin/sh
set -e
if [ ! -f certs/dev/private.pem ]; then
  mkdir -p certs/dev
  openssl genrsa -out certs/dev/private.pem 2048
  openssl rsa -in certs/dev/private.pem -pubout -out certs/dev/public.pem
fi
python -c "from app.core.config import settings; print(f'DB target: {settings.database_host}:{settings.db_port}')"
alembic upgrade head
python scripts/seed.py || { echo "ERROR: seed.py failed"; exit 1; }
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
