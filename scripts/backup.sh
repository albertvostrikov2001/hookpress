#!/usr/bin/env bash
set -euo pipefail
docker compose exec -T postgres pg_dump -U "${POSTGRES_USER:-hookpress}" "${POSTGRES_DB:-hookpress}" > "backup-$(date +%Y%m%d-%H%M%S).sql"
echo "Backup written."
