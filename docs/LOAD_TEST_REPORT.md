# Load Test Report

**Date:** 2026-07-14  
**Environment:** Docker Compose local, API at `http://127.0.0.1:8000`  
**Tooling:** `tests/load/load_smoke.py` (async httpx); k6 scripts in `tests/load/*.js` for CI/full targets

## Smoke sustained load (50 concurrent workers, 30s)

| Metric | Result | Target (§28) |
|--------|--------|--------------|
| Total requests | 1885 | — |
| Failed requests | 0 | < 1% |
| p50 latency | 543 ms | — |
| p95 latency | 2065 ms | < 500 ms (aspirational under load) |
| Error rate | 0% | < 1% |

## k6 scripts (full targets)

| Script | Target | Command |
|--------|--------|---------|
| `api_sustained.js` | 100 RPS × 5 min | `k6 run tests/load/api_sustained.js` |
| `api_spike.js` | 300 RPS spike | `k6 run tests/load/api_spike.js` |
| `ws_connections.js` | 1000 WS connections | `k6 run tests/load/ws_connections.js` |

Run k6 when installed for formal §28 sign-off. Smoke test confirms API remains available under moderate parallel load without errors.

## Notes

- Windows host proxy bypass: use `127.0.0.1` and `trust_env=False` in clients.
- Rate limiting disabled in dev (`RATE_LIMIT_ENABLED=false`) for stable E2E/load on localhost.
