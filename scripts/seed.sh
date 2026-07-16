#!/usr/bin/env bash
set -euo pipefail
docker exec -w /app -e PYTHONPATH=/app hookpress-api-1 python scripts/seed.py
echo "Seed complete."
