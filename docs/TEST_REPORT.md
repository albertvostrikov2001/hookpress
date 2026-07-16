# Test Report

**Generated:** 2026-07-14 (final acceptance)  
**Environment:** Docker Compose + Windows host E2E

## Backend (services/api)

| Suite | Command | Result |
|-------|---------|--------|
| Unit + integration | `py -3.12 -m pytest -q` (local) | **76 passed**, 2 skipped |
| Docker | `docker exec -w /app hookpress-api-1 sh -c "PYTHONPATH=/app pytest -q"` | **76 passed**, 2 skipped |

## E2E (tests/e2e) — §27 all scenarios

| Suite | Command | Result |
|-------|---------|--------|
| E2E | `$env:HOOKPRESS_API_URL="http://127.0.0.1:8000"; $env:HOOKPRESS_BUYER_EMAIL="admin@example.com"; py -3.12 -m pytest tests/e2e -m e2e -q` | **31 passed** |

## E2E scenario checklist (§27)

| # | Scenario | Status |
|---|----------|--------|
| 1 | OAuth/dev-login → refresh → logout | ✅ |
| 2 | Text → audio → Office | ✅ |
| 3 | Multipart upload resume | ✅ |
| 4 | Release → validate → score | ✅ |
| 5 | Kwork order escrow | ✅ |
| 6 | Dispute partial refund | ✅ |
| 7 | Duplicate webhook | ✅ |
| 8 | S3 access denied | ✅ |
| 9 | Chat Redis integration | ✅ |
| 10 | WebSocket reconnect | ✅ |
| 11 | Illegal state transition | ✅ |
| 12 | AI provider failure isolated | ✅ |
| 13 | Catalog independent of promo | ✅ |
| 14 | Mock mode without API keys | ✅ |

## Load (tests/load)

| Suite | Result |
|-------|--------|
| Smoke 50 workers × 30s | 1885 req, 0 failed — see `docs/LOAD_TEST_REPORT.md` |

## Go (services/promo)

| Suite | Command | Result |
|-------|---------|--------|
| Unit | `go test ./...` (CI) | pass |

## Web (apps/web)

| Suite | Command | Result |
|-------|---------|--------|
| Build | Docker `hookpress-web` image | pass (healthy :3000) |

## Flutter (apps/mobile)

| Suite | Command | Result |
|-------|---------|--------|
| Analyze | CI `flutter analyze` | pass (CI) |
| Widget tests | `flutter test` | login_screen_test (CI) |

## Security (tests/security)

| Suite | Result |
|-------|--------|
| SSRF + auth headers | pass (via API test suite) |

**Sign-off:** All critical test gates green for local MVP.
