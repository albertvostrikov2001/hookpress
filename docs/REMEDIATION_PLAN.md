# Remediation Plan — hook.press Audit

**Created:** 2026-07-15  
**Updated:** 2026-07-15 (100% MVP sign-off)  
**Source:** Audit protocol vs Master Prompt §0–§34  
**Priority order:** Blocker → High → Medium → Low

## Blockers (Definition of Done / sign-off honesty)

| ID | Gap | Action | Owner domain | Status |
|----|-----|--------|--------------|--------|
| BL-01 | `FINAL_COMPLIANCE_REPORT.md` missing | Create after full matrix verification | docs | ✅ Done |
| BL-02 | `ACCEPTANCE_MATRIX` was over-claimed (100% ✅) | Rebuilt with evidence per row | docs | ✅ Done |
| BL-03 | `test_moderation_approve` flaky (duplicate slug) | Unique slug per run | feed/tests | ✅ Done |
| BL-04 | Chart `demo-top-40` not seeded → UI empty | Seed pipeline in `scripts/seed.py` | feed/charts | ✅ Done |

## High

| ID | Gap | Action | Domain | Status |
|----|-----|--------|--------|--------|
| HI-01 | Production OAuth (Google/Yandex/VK) | MOCK-ONLY; `PRODUCTION_INTEGRATIONS.md` | auth | ⏸ Deferred (production) |
| HI-02 | Real PSP / KYC / payouts | MOCK-ONLY by design (TODO-003) | billing | ⏸ Deferred (production) |
| HI-03 | RBAC scopes not on all mutating routes | `require_scopes` on studio/market/office writes | auth | ✅ Done |
| HI-04 | AI Task state machine (§23) | `StateMachine` + tests | studio | ✅ Done |
| HI-05 | Payment state machine (§23) | `MockPaymentProvider` SM | billing | ✅ Done |
| HI-06 | Chart Redis cache + position history | Redis cache + `position_change` | charts | ✅ Done |
| HI-07 | LibROSA scoring E2E proof | E2E metrics in report payload | studio/office | ✅ Done |
| HI-08 | Flutter WS chat + real player | `chat_ws_service.dart`, `just_audio` player | mobile | ✅ Done |
| HI-09 | WCAG 2.1 AA | Skip link, landmarks, focus-visible, `WCAG_AUDIT.md` | web | ✅ Done |
| HI-10 | OTel active in default compose | Jaeger service + OTLP env on API | observability | ✅ Done |

## Medium

| ID | Gap | Action | Domain | Status |
|----|-----|--------|--------|--------|
| MD-01 | Login history API | GET `/users/me/login-events` | auth | ✅ Done |
| MD-02 | Chat presence/typing/read tests | `tests/integration/test_chat_*` | chat | ✅ Done |
| MD-03 | Rate limit automated tests | `test_rate_limit.py` | security | ✅ Done |
| MD-04 | Chart admin weight tests | `test_chart_admin_weights.py` | charts | ✅ Done |
| MD-05 | Feed articles APPROVED in seed | `moderation_status=APPROVED` in seed | feed | ✅ Done |
| MD-06 | Promo durable store | Postgres-backed campaigns (optional P2) | promo | ⏸ Deferred (P2) |
| MD-07 | Integration test coverage | 6 files in `tests/integration/` | tests | ✅ Done |
| MD-08 | FINAL_REQUIREMENTS_REPORT stale | Superseded by FINAL_COMPLIANCE_REPORT | docs | ✅ Done |

## Low

| ID | Gap | Action | Domain | Status |
|----|-----|--------|--------|--------|
| LO-01 | Apple Sign-In stub | `AppleOAuthProvider` + `test_apple_oauth.py` | auth | ✅ Done (stub) |
| LO-02 | Antivirus real scanner | ClamAV integration (TODO-008) | media | ⏸ Deferred (production) |
| LO-03 | Studio page RU hardcode | `useTranslations("studio")` | web | ✅ Done |
| LO-04 | Grafana / Jaeger docs | README monitoring + Jaeger in compose | infra | ✅ Done |
| LO-05 | Load 100 RPS formal k6 | `tests/load/*.js` scripts + README | tests | ✅ Done (scripts); sustained 100 RPS optional |

## MVP sign-off status

**All actionable HI/MD/LO items for local docker-compose MVP are complete.**  
Production-only integrations (real OAuth keys, PSP, DDEX, licensed charts, ClamAV) remain **MOCK-ONLY** per ADR-013 — not gaps for MVP.

## Verification commands

```powershell
cd C:\Work\Hook.press
docker compose up -d --build
docker exec -w /app hookpress-api-1 alembic upgrade head
docker exec -w /app -e PYTHONPATH=/app hookpress-api-1 python scripts/seed.py

# API (local source)
cd services\api
$env:PYTHONPATH=(Get-Location)
py -3.12 -m pytest -q

# Integration (requires compose Redis/Postgres on localhost)
cd C:\Work\Hook.press
$env:PYTHONPATH="services/api"
py -3.12 -m pytest tests/integration -m integration -q

# E2E
$env:HOOKPRESS_API_URL="http://127.0.0.1:8000"
py -3.12 -m pytest tests/e2e -m e2e -q
```

Jaeger UI: http://localhost:16686
