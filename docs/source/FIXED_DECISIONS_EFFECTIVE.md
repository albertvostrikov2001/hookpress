# Fixed Decisions (Effective — synthesized)

> Original «Документ зафиксированных решений» was not attached. This file records **binding decisions** derived from the master prompt and `docs/DECISIONS.md` until the official document arrives.

## Legal & compliance (non-negotiable)

1. **No stream manipulation** — no artificial DSP metrics, emulator farms, antifraud bypass, CAPTCHA bypass, proxy masking (master prompt §1).
2. **Go promo service** — legal promotion and analytics only (ADR-002).
3. **Test UPC/ISRC** — always labeled non-official; prefix `TEST-`.

## Product scope (MVP)

4. **Local run without commercial API keys** — mock providers default (ADR-006, ADR-007, ADR-005).
5. **Real payouts / KYC / AML** — out of MVP; ledger logic production-grade (ADR-005).
6. **Roles** — artist, performer (coexist), moderator, admin (admin-assigned only) (ADR-010).
7. **Default locale** — `ru`, secondary `en` (ADR-011).
8. **Mobile** — admin, complex release builder, extended CMS remain web-first (master prompt §22).

## Architecture

9. **Monorepo** — FastAPI modular monolith + isolated Go promo (ADR-003).
10. **JWT** — RS256, 15 min access, 30 day refresh with rotation (ADR-009).
11. **ClickHouse** — promo analytics aggregation (ADR-008).
12. **Scoring** — LibROSA heuristics in Celery for MVP; advisory only, not hit prediction (master prompt §11).

## Technology

13. Version matrix locked in `docs/ARCHITECTURE.md` (ADR-004).
14. pnpm workspaces for JS/TS; per-service Python/Go/Flutter locks (ADR-012).

## Conflict resolution

When Master-ТЗ (if later provided) conflicts with this document or master prompt §1, **§1 legal override and this file win**.
