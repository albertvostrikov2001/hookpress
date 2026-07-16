# hook.press — Implementation Plan

## Conflict Matrix

| Topic | Master prompt (effective) | Assumed Master TZ risk | Resolution |
|-------|---------------------------|------------------------|------------|
| Stream boosting | **Forbidden** | May describe play inflation | Legal promo module only (ADR-002) |
| Emulator farms | **Forbidden** | Possible automation | Internal voluntary listening only |
| Go service purpose | Campaign orchestration + analytics | Possible bot service | Isolated promo service, no external DSP manipulation |
| External API keys | Not required for local run | May assume live APIs | Mock adapters default (ADR-006, ADR-007) |
| Payments | Mock/sandbox MVP | May assume live PSP | Ledger complete; payouts deferred (ADR-005) |
| Chart data | Mock/demo when unlicensed | May assume scraping | Official APIs/RSS only; mock sources labeled |
| CAPTCHA/proxy bypass | **Forbidden** | — | Not implemented |
| Fixed decisions doc | Highest priority | N/A | **Effective doc** at `docs/source/FIXED_DECISIONS_EFFECTIVE.md`; supersede when original received (ADR-013) |
| Master-ТЗ doc | Second priority | N/A | **Effective doc** at `docs/source/MASTER_TZ_EFFECTIVE.md`; supersede when original received (ADR-013) |

## Stages Overview

| Stage | Name | Key deliverables | Exit criteria |
|-------|------|------------------|---------------|
| 0 | Analysis & architecture | This plan, ARCHITECTURE, DECISIONS, SECURITY, ACCEPTANCE_MATRIX | Docs complete |
| 1 | Monorepo & infra | Workspace, Docker Compose, PG/Redis/MinIO, CI, linters | `docker compose up` health checks pass |
| 2 | Backend foundation | FastAPI skeleton, DB, migrations, errors, logging, provider stubs | API `/health` + migration apply |
| 3 | Auth | OAuth mock, JWT RS256, refresh rotation, RBAC, tests | Auth E2E #1 |
| 4 | IT Studio | Lyrics, versions, AI tasks, SSE, mock LLM/audio, web UI | E2E #2 |
| 5 | Media & Office | Multipart upload, office projects, scoring, distribution mock | E2E #3, #4, #8 |
| 6 | Market & Billing | Kworks, ledger, escrow, chat, disputes | E2E #5, #6, #7 |
| 7 | Feed & Community | CMS, charts, WebSocket chat, Redis horizontal test | E2E #9, #10 |
| 8 | Legal Promo (Go) | Campaigns, ClickHouse, internal analytics | Promo API + tests |
| 9 | Flutter | Auth, feed, projects, player, chat | `flutter analyze` clean |
| 10 | Hardening | OTel, rate limits, security headers, backups | Security checklist |
| 11 | Acceptance | Full E2E, load, docs audit | ACCEPTANCE_MATRIX green |

## Stage 1 Detail (current next)

1. Root monorepo structure per ARCHITECTURE
2. `docker-compose.yml` — postgres, redis, minio, api (stub), web (stub), celery (stub), promo (stub)
3. `.env.example` with all variables documented
4. GitHub Actions: lint + typecheck + test matrix
5. Shared packages: `api-contracts`, `shared-types`, `config`, `ui` (minimal)
6. Health checks on all containers
7. `scripts/dev-up.sh` / PowerShell equivalent
8. README local setup guide

## Stage 2 Detail

1. FastAPI app factory, settings via pydantic-settings
2. Async SQLAlchemy + Alembic init migration (users, audit)
3. Unified error handler, correlation ID middleware
4. Provider interface stubs in `infrastructure/providers/`
5. pytest + httpx AsyncClient smoke tests

## Dependency Graph (stages)

```
0 → 1 → 2 → 3 → 4 → 5 → 6 → 7
              ↘       ↗
                8 (parallel after 5)
1 → 9 (after 3+7 APIs stable)
1 → 10 (after 7)
* → 11
```

## Risk Register

| Risk | Mitigation |
|------|------------|
| Missing full TZ | Document assumptions in DECISIONS; conservative defaults |
| Scope too large for one session | Incremental stages; IMPLEMENTATION_STATE handoff |
| Flutter CI on Windows | Use Linux runner in GitHub Actions |
| LibROSA in Celery image | Dedicated worker Dockerfile with audio deps |

## Commands Reference

```bash
# Local (after Stage 1)
docker compose up -d
docker compose ps
docker compose logs -f api

# Backend (after Stage 2)
cd services/api && alembic upgrade head && pytest

# Web (after Stage 1)
pnpm install && pnpm --filter web build
```
