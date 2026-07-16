# Architectural & Product Decisions (ADR Log)

> Priority: Fixed-decisions doc (not provided) > Master prompt > this log > assumptions.

## ADR-001: Source documents availability

**Status:** Superseded by ADR-013  
**Context:** Master prompt references two attached documents (Master TZ + Fixed Decisions). Only `hookpress_cursor_master_prompt.md` was available in the workspace.  
**Decision:** Derive requirements exclusively from the master prompt (sections 0–34). Any conflict with hypothetical Master TZ is resolved in favor of the master prompt's explicit legal-compliance override (section 1).  
**Consequences:** Full product spec may be incomplete; gaps filled with conservative, production-safe defaults documented here.

## ADR-013: Effective source documents (synthesized)

**Status:** Accepted  
**Context:** Original Master-ТЗ and Fixed Decisions attachments remain unavailable. Implementation must not block on external documents.  
**Decision:** Publish effective specifications in `docs/source/MASTER_TZ_EFFECTIVE.md` and `docs/source/FIXED_DECISIONS_EFFECTIVE.md`, synthesized from master prompt §7–§22 and ADR log. Maintain conflict matrix in `docs/IMPLEMENTATION_PLAN.md`. When originals arrive, diff against effective docs and update ADR-001 chain.  
**Consequences:** TODO-001 close condition updated; traceability via `docs/REQUIREMENTS_TRACE.md`.

## ADR-002: Illegal mechanics replacement

**Status:** Accepted (mandatory)  
**Context:** Master prompt section 1 forbids stream manipulation, emulator farms, antifraud bypass, etc.  
**Decision:** Go `promo` service implements **legal promotion only**: internal ad campaigns, editorial placements, voluntary promo listening, feedback collection, transparent analytics. No external DSP metric inflation.  
**Consequences:** Original TZ wording (if any) describing forbidden mechanics is ignored.

## ADR-003: Repository layout

**Status:** Accepted  
**Decision:** Monorepo at `hook-press/` per master prompt section 5. FastAPI as modular monolith; Go promo as isolated service.  
**Consequences:** Single `docker compose up` orchestrates all services.

## ADR-004: Technology versions (locked for MVP)

**Status:** Accepted — see version table in `ARCHITECTURE.md`.

## ADR-005: Payment & payouts scope

**Status:** Accepted  
**Decision:** Double-entry ledger with mock/sandbox `PaymentProvider`. Real payouts, KYC/AML, and production PSP excluded from MVP — documented in `KNOWN_LIMITATIONS.md`.  
**Consequences:** Escrow flow is fully testable locally without commercial API keys.

## ADR-006: OAuth providers for local dev

**Status:** Accepted  
**Decision:** Production OAuth: Google, Yandex, VK (+ Apple-ready architecture). Local dev: `dev-login` endpoint + seed users; OAuth adapters use mock provider when client secrets absent.  
**Consequences:** No external OAuth keys required for `docker compose up`.

## ADR-007: AI & audio providers

**Status:** Accepted  
**Decision:** Interface + provider pattern. Default: `MockLLMProvider`, `MockAudioProvider`. Claude/OpenAI/YandexGPT wired via env switch.  
**Consequences:** Studio workflow runs end-to-end without API keys.

## ADR-008: ClickHouse usage

**Status:** Accepted  
**Decision:** ClickHouse included in Docker Compose for promo analytics aggregation (Stage 8). FastAPI core uses PostgreSQL only until promo service needs event sink.  
**Consequences:** Extra container in compose; optional lightweight profile can disable it pre-Stage-8.

## ADR-009: JWT signing

**Status:** Accepted  
**Decision:** RS256 with auto-generated dev keypair in `infra/docker/certs/` (gitignored); production expects mounted secrets.  
**Consequences:** Keys regenerated on fresh clone unless persisted in volume.

## ADR-010: Missing fixed-decisions doc — auth roles

**Status:** Accepted  
**Decision:** Roles: `artist`, `performer`, `moderator`, `admin`. Artist and performer may coexist on one user. Admin assigned only via admin API/seed.  
**Consequences:** RBAC tables include role junction with scope checks on every mutating endpoint.

## ADR-011: i18n default locale

**Status:** Accepted  
**Decision:** Default `ru`, secondary `en`. Cookie/header `Accept-Language` + explicit user preference.  
**Consequences:** All user-facing strings externalized from Stage 4 web UI onward.

## ADR-012: Monorepo package manager

**Status:** Accepted  
**Decision:** pnpm workspaces for JS/TS; Python per-service with `uv` or `pip` + `requirements.lock`; Go modules; Melos optional later — Flutter uses standard `pubspec.lock`.  
**Consequences:** Root `pnpm-workspace.yaml` + per-app lockfiles.
