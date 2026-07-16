# Final Design Checklist — hook.press

**Date:** 2026-07-15  
**Spec:** `docs/source/CURSOR_DESIGN_PROMPT.md`  
**Sign-off:** Design Completion **100%**

## Global navigation

| Requirement | Status |
|-------------|--------|
| Dashboard, Studio, Office, Market, Feed, Charts, Chat | ✅ |
| Notifications, Profile, Promo | ✅ |
| Moderator / Admin (role-gated) | ✅ |
| Role badge, global search, unread notifications | ✅ |
| i18n ru/en | ✅ |

## Screens (all 4 states: loading / empty / error / populated)

| Screen | Ready | Notes |
|--------|-------|-------|
| Dashboard | ✅ | Summary cards, empty CTA |
| IT Studio | ✅ | Waveform, ProgressRail, editor |
| Office | ✅ | Stepper, scoring, distribution, upload |
| Market catalog | ✅ | Filters, previews, pagination N/A |
| Kwork detail | ✅ | Cover, portfolio, publish, order |
| Order detail | ✅ | Chat, specs, dispute link |
| Market account | ✅ | Wallet, ledger, orders |
| Performer profile | ✅ | Kworks list |
| Dispute detail | ✅ | Evidence |
| Feed list | ✅ | Categories, tags, load more |
| Feed article | ✅ | SEO, actions, comments |
| Charts | ✅ | Position delta |
| Chat | ✅ | Rooms, WS, profile links |
| Promo | ✅ | Campaigns CRUD list |
| Notifications | ✅ | Filters |
| Profile | ✅ | Sessions, login history |
| Admin feed | ✅ | Drafts, RSS ingest |
| Admin charts | ✅ | Weights JSON |
| Admin audit | ✅ | Log viewer |
| Moderator | ✅ | Dispute queue |
| Home | ✅ | Marketing landing |

## Design system

| Item | Doc |
|------|-----|
| Palette, typography, layout | `docs/DESIGN_SYSTEM.md` |
| Screen audit | `docs/UI_AUDIT.md` |
| Implementation state | `docs/IMPLEMENTATION_STATE.md` |

## Local deploy (quick start)

```powershell
cd C:\Work\Hook.press

# 1. Start stack
docker compose up -d --build

# 2. Migrations + seed (first run or after schema change)
docker exec -w /app hookpress-api-1 alembic upgrade head
docker exec -w /app -e PYTHONPATH=/app hookpress-api-1 python scripts/seed.py

# 3. Rebuild web after UI changes
docker compose build web
docker compose up -d web
```

## URLs

| Service | URL |
|---------|-----|
| Web | http://localhost:3000 |
| API | http://localhost:8000/docs |
| Jaeger | http://localhost:16686 |
| MinIO console | http://localhost:9001 |

## Dev logins (seed)

| Email | Role |
|-------|------|
| artist@example.com | Artist |
| admin@example.com | Admin |
| moderator@example.com | Moderator |

Dev-login: `/ru/login` — no password.

## Verification commands

```powershell
# API (local)
cd C:\Work\Hook.press\services\api
$env:PYTHONPATH=(Get-Location)
py -3.12 -m pytest -q

# E2E (API must be running)
cd C:\Work\Hook.press
$env:HOOKPRESS_API_URL="http://127.0.0.1:8000"
py -3.12 -m pytest tests/e2e -m e2e -q
```

## Deferred (production-only)

See `docs/PRODUCTION_INTEGRATIONS.md` — real OAuth, PSP, ClamAV, sustained load tests.
