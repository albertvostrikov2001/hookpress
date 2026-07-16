# Requirements Traceability Matrix

Legend: ✅ Done | 🟡 Partial | ❌ Not started | ➖ N/A (deferred production)

| Prompt § | Requirement ID | Description | Component | Test | Status |
|----------|----------------|-------------|-----------|------|--------|
| 1 | LEG-01 | No stream manipulation / bots | promo, docs | compliance audit | ✅ |
| 1 | LEG-02 | Legal promo module only | services/promo | promo tests | 🟡 |
| 2 | MVP-01 | docker compose up without API keys | docker-compose.yml | e2e mock mode | ✅ |
| 5 | STR-01 | Monorepo layout | repo root | CI | 🟡 |
| 7 | BE-01 | All backend domains | services/api | pytest | 🟡 |
| 7 | BE-02 | Pagination/filtering standard | api v1 | integration | ❌ |
| 7 | BE-03 | Idempotency middleware | api | integration | 🟡 |
| 7 | BE-04 | notifications domain | api | pytest | ❌ |
| 7 | BE-05 | promotions bridge | api | pytest | ❌ |
| 8 | AUTH-01 | OAuth Google/Yandex/VK | auth | e2e #1 | 🟡 |
| 8 | AUTH-02 | Apple Sign-In ready | auth | unit | ❌ |
| 8 | AUTH-03 | JWT RS256 refresh rotation | auth | test_auth | ✅ |
| 8 | AUTH-04 | Login history | auth | pytest | ❌ |
| 8 | AUTH-05 | Session revoke one/all | auth | pytest | ❌ |
| 8 | AUTH-06 | RBAC + scopes | auth | pytest | 🟡 |
| 9 | STU-01 | Lyric versions CRUD | studio | pytest | 🟡 |
| 9 | STU-02 | Theme/mood/genre/structure | studio | pytest | ❌ |
| 9 | STU-03 | Syllables + rhyme map | studio | pytest | ❌ |
| 9 | STU-04 | Context assistant | studio | pytest | ❌ |
| 9 | STU-05 | SSE + polling fallback | studio | e2e #2 | 🟡 |
| 9 | STU-06 | Waveform + playback | studio/web | e2e | ❌ |
| 9 | STU-07 | LLM/audio adapters | providers | test_providers | 🟡 |
| 10 | OFF-01 | Release types single/EP/album | office | pytest | ❌ |
| 10 | OFF-02 | Metadata contributors explicit | office | pytest | ❌ |
| 10 | OFF-03 | Multipart resumable upload | media | e2e #3 | 🟡 |
| 10 | OFF-04 | Send-to-office idempotent | studio | e2e #2 | ✅ |
| 11 | SCR-01 | LibROSA scoring Celery | workers/celery | e2e #4 | ❌ |
| 12 | DST-01 | DistributionProvider mock | office | pytest | 🟡 |
| 12 | DST-02 | Distribution webhooks | office | pytest | 🟡 |
| 13 | MKT-01 | Kwork categories | market | pytest | 🟡 |
| 13 | MKT-02 | Search filters rating | market | pytest | 🟡 |
| 13 | MKT-03 | Order revisions deliverables | market | pytest | ❌ |
| 13 | MKT-04 | Moderator UI | web | e2e | ❌ |
| 14 | BIL-01 | Double-entry ledger | billing | pytest | ✅ |
| 14 | BIL-02 | Platform commission | billing | pytest | ❌ |
| 14 | BIL-03 | Reconciliation | billing | pytest | ❌ |
| 15 | DSP-01 | Dispute evidence immutability | disputes | pytest | 🟡 |
| 16 | FED-01 | CMS full | feed | pytest | 🟡 |
| 16 | FED-02 | Bookmarks views | feed | pytest | ❌ |
| 16 | FED-03 | RSS ingest + moderation | feed | pytest | 🟡 |
| 17 | CHT-01 | Chart pipeline + weights | charts | pytest | 🟡 |
| 17 | CHT-02 | Admin weight config | admin/web | pytest | ❌ |
| 18 | CHAT-01 | WS + Redis pub/sub | chat | e2e #9 | 🟡 |
| 18 | CHAT-02 | Presence typing read | chat | pytest | ❌ |
| 18 | CHAT-03 | Reconnect backoff | web/chat | e2e #10 | ❌ |
| 18 | CHAT-04 | Attachments | chat | pytest | ❌ |
| 19 | PRO-01 | Campaign budget schedule | promo | go test | 🟡 |
| 19 | PRO-02 | Promo listening ratings | promo | go test | ❌ |
| 19 | PRO-03 | ClickHouse aggregates | promo | go test | 🟡 |
| 20 | MED-01 | S3 private presigned | media | e2e #8 | ✅ |
| 20 | MED-02 | AV quarantine states | media | pytest | ❌ |
| 20 | MED-03 | Lifecycle cleanup | media | pytest | ❌ |
| 21 | WEB-01 | i18n ru/en | web | manual | ❌ |
| 21 | WEB-02 | Dark/light theme | web | manual | ❌ |
| 21 | WEB-03 | WCAG 2.1 AA | web | axe CI | ❌ |
| 21 | WEB-04 | SEO sitemap OG JSON-LD | web | manual | ❌ |
| 21 | WEB-05 | All pages API-connected | web | audit | 🟡 |
| 22 | MOB-01 | Flutter full feature set | mobile | flutter test | 🟡 |
| 22 | MOB-02 | Offline chat/tasks | mobile | flutter test | ❌ |
| 23 | SM-01 | All state machines enforced | domain | test_state_* | 🟡 |
| 24 | SEC-01 | Security checklist complete | SECURITY.md | security tests | 🟡 |
| 25 | OBS-01 | OpenTelemetry | api | integration | ❌ |
| 25 | OBS-02 | Grafana dashboards | infra | manual | ❌ |
| 25 | OBS-03 | Full Prometheus metrics | api | manual | 🟡 |
| 26 | INF-01 | Env profiles k8s terraform | infra | validate | 🟡 |
| 26 | INF-02 | Backup restore scripts | scripts | smoke | 🟡 |
| 27 | TST-01 | 14 E2E scenarios | tests/e2e | CI | 🟡 |
| 27 | TST-02 | Load tests | tests/load | report | ❌ |
| 27 | TST-03 | Security test suite | tests/security | CI | ❌ |
| 28 | PERF-01 | 100 RPS / 1000 WS | load report | k6 | ❌ |
| 33 | DOD-01 | Definition of Done gate | docs | CI all green | 🟡 |
| 34 | ART-01 | Final artifacts | docs/ | audit | 🟡 |

**Coverage summary:** update after each phase closure.
