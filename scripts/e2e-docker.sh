#!/usr/bin/env bash
# Run E2E tests against the Docker API (bypasses host proxy issues)
set -euo pipefail
docker exec -w /app -e PYTHONPATH=/app hookpress-api-1 pip install -q httpx pytest websocket-client 2>/dev/null || true
docker cp tests/e2e hookpress-api-1:/tmp/e2e
docker exec -e HOOKPRESS_API_URL=http://127.0.0.1:8000 \
  -e HOOKPRESS_BUYER_EMAIL=admin@example.com \
  -w /tmp/e2e hookpress-api-1 \
  sh -c "pip install -q httpx pytest websocket-client && pytest -m e2e -q"
