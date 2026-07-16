# API Overview

Base URL (local): `http://localhost:8000/api/v1`

OpenAPI: `http://localhost:8000/api/v1/openapi.json` (available after Stage 2)

## Conventions

- **Auth:** Bearer JWT or HttpOnly cookie (web)
- **Correlation:** `X-Request-ID` (client may supply; server generates if absent)
- **Idempotency:** `Idempotency-Key` header on POST mutations (payments, send-to-office)
- **Pagination:** `?page=1&page_size=20` → `{ items, total, page, page_size }`
- **Errors:** `{ "error": { "code": "...", "message": "...", "details": {} } }`

## Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness |
| GET | `/ready` | Readiness (DB, Redis, MinIO) |

## Auth (Stage 3)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/auth/oauth/{provider}/start` | OAuth redirect |
| GET | `/auth/oauth/{provider}/callback` | OAuth callback |
| POST | `/auth/dev-login` | Local dev login (disabled in prod) |
| POST | `/auth/refresh` | Refresh token rotation |
| POST | `/auth/logout` | Revoke session |
| GET | `/auth/sessions` | List active sessions |
| DELETE | `/auth/sessions/{id}` | Revoke one session |

## Users

| Method | Path | Description |
|--------|------|-------------|
| GET | `/users/me` | Current profile |
| PATCH | `/users/me` | Update profile |

## Studio (Stage 4)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/studio/projects` | Create project |
| GET | `/studio/projects/{id}` | Get project |
| POST | `/studio/projects/{id}/generate-lyrics` | Start LLM task |
| GET | `/studio/projects/{id}/tasks/{task_id}/events` | SSE progress |
| POST | `/studio/projects/{id}/send-to-office` | Idempotent office handoff |

## Office & Media (Stage 5)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/media/uploads/initiate` | Multipart upload start |
| POST | `/media/uploads/{id}/parts` | Upload part |
| POST | `/media/uploads/{id}/complete` | Complete upload |
| GET | `/office/projects` | List projects |
| POST | `/office/releases/{id}/submit` | Submit for validation |

## Market & Billing (Stage 6)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/market/kworks` | Search kworks |
| POST | `/market/orders` | Create order |
| POST | `/billing/webhooks/payment` | Payment webhook (mock) |

## Chat (Stage 7)

| WS | `/ws/chat/{room_id}` | WebSocket messages |

## Promo (Stage 8 — Go service)

Base: `http://localhost:8081/api/v1`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/campaigns` | Create campaign |
| GET | `/campaigns/{id}/stats` | Aggregated stats |

Full endpoint list will expand per stage in this document.
