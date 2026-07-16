#!/usr/bin/env bash
set -euo pipefail
FILE="${1:?usage: restore.sh backup.sql}"
docker compose exec -T postgres psql -U "${POSTGRES_USER:-hookpress}" "${POSTGRES_DB:-hookpress}" < "$FILE"
echo "Restore complete."
