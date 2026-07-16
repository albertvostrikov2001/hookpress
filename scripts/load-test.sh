#!/usr/bin/env bash
set -euo pipefail
if command -v k6 >/dev/null 2>&1; then
  k6 run tests/load/api_sustained.js
else
  echo "k6 not installed — skip load test"
fi
