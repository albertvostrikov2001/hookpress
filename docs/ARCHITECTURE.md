# hook.press — Architecture

## Version Matrix (MVP baseline)

| Component | Version | Notes |
|-----------|---------|-------|
| Node.js | 22 LTS | CI + Next.js build |
| pnpm | 9.x | Monorepo workspaces |
| Next.js | 15.1.x | App Router, React 19 |
| React | 19.x | Strict mode |
| TypeScript | 5.7.x | strict |
| Tailwind CSS | 3.4.x | Design tokens in `packages/ui` |
| Python | 3.12.x | Backend + Celery |
| FastAPI | 0.115.x | Async API |
| SQLAlchemy | 2.0.x | Async ORM |
| Alembic | 1.14.x | Migrations |
| Celery | 5.4.x | Background jobs |
| Redis | 7.2.x | Cache, Celery broker, Pub/Sub |
| PostgreSQL | 16.x | Primary datastore |
| MinIO | RELEASE.2024-12-18 | S3-compatible storage |
| Go | 1.23.x | Promo service |
| ClickHouse | 24.8 LTS | Promo analytics (Stage 8+) |
| Flutter | 3.27.x | iOS 16+, Android 10+ |
| Docker Compose | v2 | Local orchestration |
| OpenTelemetry | 1.x | Traces (Stage 10) |
| Prometheus | 2.55.x | Metrics |
| Grafana | 11.x | Dashboards |

Compatibility notes:
- Next.js 15 requires React 19; App Router only.
- SQLAlchemy 2.0 async requires `asyncpg` driver.
- Celery 5.4 supports Redis 7 as broker and result backend.
- MinIO SDK compatible with AWS S3 API v4 signatures.

## C4 — Context

```mermaid
C4Context
  title hook.press System Context
  Person(artist, "Artist / Performer", "Creates music, releases, orders kworks")
  Person(moderator, "Moderator", "Moderates content, disputes")
  Person(admin, "Admin", "Platform administration")
  System(hookpress, "hook.press Platform", "Music creation, distribution, marketplace, community")
  System_Ext(oauth, "OAuth Providers", "Google, Yandex, VK")
  System_Ext(llm, "LLM Providers", "Claude, OpenAI, YandexGPT (optional)")
  System_Ext(audio, "Audio Gen Providers", "External TTS/music (optional)")
  System_Ext(dsp, "Distribution", "DDEX/API distributors (future)")
  System_Ext(psp, "Payment PSP", "Sandbox/production (future)")

  Rel(artist, hookpress, "Uses")
  Rel(moderator, hookpress, "Moderates")
  Rel(admin, hookpress, "Administers")
  Rel(hookpress, oauth, "OAuth 2.0")
  Rel(hookpress, llm, "Lyrics/assistant (adapter)")
  Rel(hookpress, audio, "Demo generation (adapter)")
  Rel(hookpress, dsp, "Release delivery (mock MVP)")
  Rel(hookpress, psp, "Payments (mock MVP)")
```

## C4 — Containers

```mermaid
C4Container
  title hook.press Containers
  Person(user, "User")
  Container(web, "Web App", "Next.js", "SSR/CSR UI")
  Container(mobile, "Mobile App", "Flutter", "iOS/Android")
  Container(api, "API", "FastAPI", "Modular monolith")
  Container(celery, "Workers", "Celery", "AI, scoring, distribution jobs")
  Container(promo, "Promo Service", "Go", "Campaigns, analytics")
  ContainerDb(pg, "PostgreSQL", "Transactional data")
  ContainerDb(redis, "Redis", "Cache, queues, WS fanout")
  ContainerDb(minio, "MinIO", "Private media")
  ContainerDb(ch, "ClickHouse", "Event analytics")

  Rel(user, web, "HTTPS")
  Rel(user, mobile, "HTTPS")
  Rel(web, api, "REST/WebSocket")
  Rel(mobile, api, "REST/WebSocket")
  Rel(api, pg, "SQL")
  Rel(api, redis, "Cache/PubSub")
  Rel(api, minio, "S3 API")
  Rel(celery, pg, "SQL")
  Rel(celery, redis, "Broker")
  Rel(celery, minio, "Media read")
  Rel(promo, ch, "Events")
  Rel(api, promo, "HTTP internal")
```

## Domain Boundaries (FastAPI modules)

| Module | Responsibility |
|--------|----------------|
| auth | OAuth, JWT, sessions, RBAC |
| users | Profiles, roles |
| studio | Lyrics, rhythm, rhymes, AI tasks |
| media | Upload, presigned URLs, scanning |
| office | Projects, tracks, releases |
| scoring | LibROSA heuristics (Celery) |
| distribution | Provider adapter, webhooks |
| market | Kworks, orders |
| billing | Ledger, escrow |
| disputes | Arbitration flow |
| chat | Community rooms, WS |
| media_feed | CMS, articles |
| charts | Hybrid chart pipeline |
| promotions | Bridge to Go promo API |
| notifications | Email/push/in-app |
| admin | Admin operations |
| audit | Immutable audit log |

## Layering (per module)

```
api/          → routers, request/response DTOs
application/  → use cases, orchestration
domain/       → entities, state machines, invariants
infrastructure/ → SQLAlchemy repos, S3, external adapters
```

## State Machines (backend-enforced)

See master prompt §23 — implemented in domain layer with transition guards + tests.

## ER Diagram (core entities)

```mermaid
erDiagram
  users ||--o{ user_roles : has
  users ||--o{ sessions : has
  users ||--o{ studio_projects : owns
  studio_projects ||--o{ lyric_versions : has
  studio_projects ||--o{ ai_tasks : triggers
  studio_projects ||--o| office_projects : sends_to
  office_projects ||--o{ tracks : contains
  tracks ||--o{ media_assets : references
  office_projects ||--o{ releases : produces
  releases ||--o{ distribution_jobs : has
  users ||--o{ kwork_profiles : may_have
  kworks ||--o{ market_orders : generates
  market_orders ||--o{ ledger_entries : affects
  market_orders ||--o| disputes : may_have
  users ||--o{ chat_messages : sends
  chat_rooms ||--o{ chat_messages : contains
  feed_articles ||--o{ feed_comments : has
```

## Provider Interfaces

| Interface | Mock default | Production adapter |
|-----------|--------------|-------------------|
| LLMProvider | MockLLM | Claude, OpenAI, YandexGPT |
| AudioProvider | MockAudio | External API |
| DistributionProvider | MockDistributor | DDEX/API |
| PaymentProvider | MockPayment | PSP sandbox |
| ChartSource | MockChart | Licensed APIs |
| OAuthProvider | DevLogin | Google, Yandex, VK |

## API Versioning

- Public REST: `/api/v1/...`
- OpenAPI: `/api/v1/openapi.json`
- Health: `/health`, `/ready`
- Correlation: `X-Request-ID` header propagated

## Security Summary

See `SECURITY.md` for threat model. Key points: private S3, RS256 JWT, refresh rotation, RBAC on every mutation, idempotent webhooks, no float money.

## Observability

Structured JSON logs, OTel traces (Stage 10), Prometheus metrics, Grafana dashboards, Sentry-compatible error hook.
