# MASTER PROMPT ДЛЯ CURSOR — ПЛАТФОРМА hook.press

К этому промпту приложены два документа:

1. **Master-ТЗ платформы hook.press** — полное продуктовое и техническое задание.
2. **Документ зафиксированных решений** — уточнённые продуктовые и архитектурные решения.

**Приоритет источников (обязательно к соблюдению):**
1. Зафиксированные решения — высший приоритет, при конфликте всегда побеждают.
2. Master-ТЗ.
3. Общепринятые инженерные практики.
4. Самостоятельные обоснованные технические допущения (зафиксировать в `docs/DECISIONS.md`).

Не задавай пользователю вопросов. Все решения уже приняты. При обнаружении пробела в требованиях — выбери наиболее безопасный, поддерживаемый и практичный вариант, задокументируй его и продолжай работу.

---

## 0. Твоя роль

Ты работаешь как автономная senior-команда в одном лице:
software architect, backend engineer, frontend engineer, Flutter engineer, Go engineer, database engineer, security engineer, DevOps engineer, QA automation engineer, technical writer.

Ты обязан:
- принимать инженерные решения самостоятельно и документировать их;
- не останавливать работу и не запрашивать подтверждения без крайней необходимости;
- при отсутствии внешних ключей/аккаунтов/партнёрских договоров — использовать mock/sandbox-адаптеры, а не блокировать прогресс;
- не удалять существующий рабочий код без необходимости;
- в конце каждой сессии обновлять `docs/IMPLEMENTATION_STATE.md`.

## 1. Обязательная корректировка исходного ТЗ (жёсткое ограничение)

Категорически запрещено реализовывать:
- накрутку прослушиваний;
- фермы эмуляторов;
- искусственное увеличение метрик DSP;
- обход антифрод-систем сторонних платформ;
- резидентные прокси для маскировки автоматизации;
- обход CAPTCHA;
- сокрытие автоматизированного поведения;
- любые механизмы нарушения правил сторонних платформ.

Вместо этого реализуй **легальный модуль продвижения**: рекламные кампании, внутренние промо-размещения, creator collaborations, рекомендательные механики, добровольное тестирование треков, сбор обратной связи, прозрачная аналитика кампаний, внутренний промо-плеер без искусственного влияния на DSP.

Go-сервис — изолированный сервис оркестрации рекламных кампаний и высоконагруженной аналитики, **не** сервис накрутки.

Если Master-ТЗ где-либо описывает запрещённые механики — они автоматически заменяются легальными аналогами, независимо от формулировок ТЗ.

## 2. Цель

Построить реально запускаемый **production-ready MVP**, а не макет, прототип, псевдокод или набор заглушек. Проект должен полностью подниматься локально через `docker compose up` без каких-либо коммерческих API-ключей. Внешние интеграции — через заменяемые адаптеры (interface + provider) с локальными mock-реализациями по умолчанию.

## 3. Стратегия и дисциплина реализации

Не пытайся сделать всё одним изменением. Работай инкрементально по этапам (см. раздел 12). Каждый этап должен оставлять репозиторий в рабочем состоянии.

После каждого этапа обязательно:
1. форматирование (prettier/black/gofmt/dart format);
2. линтеры (eslint, ruff/flake8, golangci-lint, flutter analyze);
3. type-check (tsc --noEmit, mypy при необходимости);
4. релевантные тесты;
5. production build (web, backend образ, Go binary, Flutter build);
6. исправление найденных ошибок;
7. обновление документации;
8. обновление `docs/IMPLEMENTATION_STATE.md`.

Если упираешься в лимит контекста — заверши текущую атомарную задачу, сохрани состояние репозитория рабочим, обнови `IMPLEMENTATION_STATE.md` с точной инструкцией для продолжения. Никогда не оставляй репозиторий в сломанном состоянии.

## 4. Постоянные артефакты состояния (создать и поддерживать всегда)

```
docs/IMPLEMENTATION_PLAN.md
docs/IMPLEMENTATION_STATE.md
docs/ARCHITECTURE.md
docs/DECISIONS.md
docs/ACCEPTANCE_MATRIX.md
docs/SECURITY.md
docs/DEPLOYMENT.md
docs/API.md
docs/KNOWN_LIMITATIONS.md
```

`IMPLEMENTATION_STATE.md` обязателен и должен содержать: текущий этап, выполненные задачи, открытые задачи, результаты проверок, известные проблемы, следующие действия, список mock-интеграций, список production-интеграций, команды для продолжения работы. Это главный источник состояния между сессиями.

## 5. Архитектура монорепозитория

```
hook-press/
  apps/
    web/
    mobile/
  services/
    api/
    promo/
  workers/
    celery/
  packages/
    api-contracts/
    shared-types/
    ui/
    config/
  infra/
    docker/
    kubernetes/
    terraform/
    monitoring/
  docs/
  tests/
    integration/
    e2e/
    load/
    security/
  scripts/
```

Структуру можно уточнить, но нельзя превращать MVP в преждевременную микросервисную архитектуру. FastAPI Core — модульный монолит с чёткими доменными границами. Go-сервис — изолированный сервис легального продвижения и аналитики.

## 6. Технологический стек

Используй актуальные стабильные совместимые версии на момент реализации. Beta/canary/experimental — запрещены без явного обоснования в `docs/DECISIONS.md`. Все версии фиксируются lock-файлами (package manager, Python, Flutter, Go modules, Docker image tags).

Базовый стек: Next.js, React, TypeScript, Tailwind CSS, Flutter, FastAPI, Python, PostgreSQL, SQLAlchemy, Alembic, Celery, Redis, MinIO/S3, Go, ClickHouse (когда действительно нужен), Docker Compose, GitHub Actions, OpenTelemetry, Prometheus, Grafana, Sentry-compatible error tracking.

Перед генерацией кода создай таблицу выбранных версий (`docs/ARCHITECTURE.md`) и объясни критичные решения совместимости.

## 7. Backend (FastAPI) — модульный монолит

Домены: auth, users, studio, media, office, releases, scoring, distribution, market, billing, disputes, chat, community, media_feed, charts, promotions, notifications, admin, audit.

Требования: async endpoints где оправдано; разделение API/application/domain/infrastructure; dependency injection; Pydantic-схемы; SQLAlchemy-модели; Alembic-миграции; единый формат ошибок; correlation ID; idempotency keys; audit logging; pagination; фильтрация; versioned API; OpenAPI; health/readiness endpoints. Не создавай лишних абстракций, но обеспечь заменяемость внешних провайдеров через интерфейсы.

## 8. Авторизация

OAuth 2.0 Authorization Code Flow: Google, Яндекс, VK; архитектурная готовность Apple Sign-In. JWT RS256, access token 15 минут, refresh token 30 дней, refresh rotation, обнаружение повторного использования refresh token, отзыв сессий (одна/все), журнал входов. HttpOnly Secure SameSite cookie для web; secure storage strategy для Flutter. RBAC + scopes + backend authorization checks (UI-проверка никогда не заменяет backend).

Роли: Artist, Performer (могут совмещаться у одного пользователя), Moderator, Admin (только административное назначение).

Для локального запуска — безопасный dev-login/seed-пользователи, без ослабления production-конфигурации.

## 9. ИТ-Студия

Сквозной сценарий: генерация текста → ручное редактирование → анализ ритма → подбор рифм → контекстный чат → создание аудиодемо → отслеживание прогресса → прослушивание → отправка в Офис.

Функции: тема (до 200 символов), настроение, жанр, конструктор структуры, версии текста, подсчёт слогов, карта рифм, двухпанельный редактор, контекстные изменения фрагментов, async audio generation через Celery/Redis, SSE для прогресса + polling fallback, waveform, MP3, WAV только если провайдер реально отдаёт WAV, хранение оригиналов и производных media assets, mock LLM, mock audio generator.

Адаптеры (интерфейс + реализация): Claude, OpenAI, YandexGPT, external audio provider, local mock provider. Отсутствие ключей не блокирует запуск — по умолчанию используются mock-провайдеры.

## 10. Офис

Проекты, синглы, EP, альбомы, треки, версии медиа, метаданные, contributors, explicit marker, даты релиза, импорт из ИТ-Студии. S3 Multipart Upload с resumable upload, контрольными суммами, восстановлением после разрыва сети. Серверная валидация WAV и обложек. Фоновые задачи скоринга. Mock distribution provider. Статусы релизов. Тестовые UPC/ISRC с явной маркировкой как тестовых.

Кнопка «Отправить в Офис»: создаёт Office Project, присваивает `DRAFT_IN_OFFICE`, сохраняет связи с immutable media assets без физического копирования S3-объектов без необходимости, выполняется транзакционно и идемпотентно.

## 11. AI Audio Scoring

MVP — объяснимая эвристическая модель на LibROSA, выполняемая в Celery worker (не блокирует API). Не заявлять, что система объективно предсказывает хит.

Отчёт включает: BPM, key, spectral centroid, динамический диапазон, длительность интро, показатели громкости (если корректно измерены), жанровые диапазоны, итоговый вспомогательный score, уровень уверенности, причины оценки, текстовые рекомендации, ограничения анализа. Архитектура должна допускать подключение проверенной ML-модели позже.

## 12. Дистрибуция

Интерфейс `DistributionProvider` + mock-distributor: сборка пакета метаданных, статусы доставки, журнал запросов, повторные попытки, идемпотентность, обработка webhook, тестовые UPC/ISRC, интерфейс будущего DDEX/API-адаптера. Внутренние тестовые коды никогда не выдаются за официальные.

## 13. Маркет

Категории кворков (MVP: дизайн, продакшн, звукорежиссура, сонграйтинг), профили исполнителей, создание/редактирование кворков, поиск, фильтры, рейтинг, портфолио, защищённые media previews, заказы, версии ТЗ заказа, чат сделки, файлы, сдача результата, ревизии, приёмка, dispute flow, интерфейс модератора.

## 14. Billing и Escrow

Double-entry ledger. Требования: никаких денежных значений в float — только integer minor units или Decimal; ledger entries immutable; каждая операция идемпотентна; уникальные внешние transaction IDs; защита от повторных webhook; row locking/корректный concurrency control; сверка балансов; hold/capture/refund/partial refund; platform commission; performer payable balance; audit trail.

`PaymentProvider` interface + sandbox/mock provider. Реальные выплаты не считаются включёнными без легитимного провайдера, KYC/AML и договорной схемы — зафиксировать это явно в `KNOWN_LIMITATIONS.md`.

## 15. Арбитраж

Открытие спора, заморозка состояния заказа, запрет редактирования/удаления сообщений после открытия спора, доказательства, история решений, частичное распределение, полный/частичный refund, частичная выплата, роли модератора, audit logging, транзакционность финансового решения.

## 16. Лента

Редакционная CMS: статьи, категории, теги, авторы, черновики, публикация, RSS/API ingest, модерация импортированных материалов, пагинация, лайки, закладки, просмотры, комментарии, SEO. Только официальные API, RSS, партнёрские выгрузки и разрешённые источники. Запрещены CAPTCHA bypass и маскировка парсеров.

## 17. Гибридный чарт

Расширяемый pipeline агрегации: интерфейс источника, normalized chart entries, source weights, история позиций, расчёт динамики, new entry, Redis cache, фоновые обновления, mock chart sources, административная настройка весов. Алгоритм документирован и воспроизводим. При отсутствии лицензированных источников — демонстрационные данные с явной маркировкой.

## 18. Community Chat

Комнаты, сообщения, presence, typing, read status, WebSocket, Redis Pub/Sub, горизонтальное масштабирование, история сообщений, пагинация, reconnect с exponential backoff, deduplication по client-generated message ID, optimistic UI, доступ к профилю, переход к кворкам пользователя, защищённые вложения.

Обязателен integration test: два backend-инстанса обмениваются сообщениями через Redis.

## 19. Легальное продвижение (Go-сервис)

Создание рекламных кампаний, таргетируемые внутренние размещения, управление лимитами бюджета, расписание кампаний, сбор событий, агрегация аналитики, rate limiting, idempotency, передача агрегатов в ClickHouse, API статистики, внутренний добровольный promo-listening, пользовательские оценки треков, антифрод внутренней системы. Категорически запрещены любые механизмы искусственных стримов на внешних платформах.

## 20. Media и S3

Все бакеты приватные. Pre-signed URLs с ограниченным TTL и проверкой прав перед выдачей. S3 Multipart Upload, MIME sniffing, контроль размера, checksum, безопасные object keys, антивирусный карантин, состояния upload/scanning/ready/rejected, lifecycle cleanup, immutable media versions, запрет прямого публичного доступа.

Обязателен тест, подтверждающий невозможность получения чужого файла.

## 21. Web-приложение (Next.js)

App Router, TypeScript strict mode, Tailwind, переиспользуемый UI-пакет, дизайн-токены, dark/light theme, responsive layouts, WCAG 2.1 AA, формы с серверной и клиентской валидацией, loading/error/empty states, route protection, i18n (русский, английский), SSR/ISR для публичных страниц, sitemap, robots.txt, canonical, Open Graph, JSON-LD, human-readable slugs, оптимизация Core Web Vitals. Никаких декоративных страниц без подключения к API — все ключевые экраны работают со сквозным backend flow.

## 22. Flutter

Авторизация, secure token storage, refresh flow, профиль, Лента, проекты, статусы фоновых задач, аудиоплеер, waveform, чат с reconnect, базовое редактирование, i18n, error handling, offline-tolerant state для чата и задач. Админ-панель, сложный конструктор релиза и расширенная CMS остаются web-first. Поддержка: iOS 16+, Android 10+.

## 23. State machines (обязательные, backend-enforced)

```
AI Task:
PENDING → PROCESSING → SUCCEEDED | FAILED | CANCELLED

Office Project:
DRAFT_IN_STUDIO → DRAFT_IN_OFFICE → READY_FOR_RELEASE

Release:
DRAFT → VALIDATING → MODERATION → DELIVERED → RELEASED
      → REJECTED | FAILED

Market Order:
CREATED → AWAITING_PAYMENT → FUNDS_HELD → IN_PROGRESS
        → DELIVERED → COMPLETED
        → IN_DISPUTE → REFUNDED | PARTIALLY_REFUNDED | CANCELLED

Payment:
CREATED → PENDING → AUTHORIZED → CAPTURED
        → PARTIALLY_REFUNDED | REFUNDED | FAILED

Dispute:
OPEN → UNDER_REVIEW → RESOLVED → CLOSED
```

Недопустимые переходы блокируются backend и покрываются тестами.

## 24. Безопасность

TLS-ready configuration, JWT RS256, refresh rotation, secure cookies, CSRF-защита где применимо, CORS allowlist, CSP, rate limiting, brute-force protection, input validation, защита от SQL injection/XSS/SSRF, webhook signature validation, replay protection, секреты только через env/secret manager, безопасная обработка файлов, RBAC, audit logs, least privilege, dependency scanning, security headers, исключение секретов из логов, персональные данные не попадают в telemetry без необходимости. Не разрабатывать собственную криптографию.

Подготовить threat model для: auth, payments, file access, marketplace, chat, webhooks, AI integrations (`docs/SECURITY.md`).

## 25. Наблюдаемость

JSON logs, request/correlation/trace ID, OpenTelemetry, Prometheus metrics, Grafana dashboards, error tracking integration, Celery monitoring, queue depth metrics, WebSocket metrics, payment metrics, storage metrics, health/readiness checks. Логи не должны содержать токены, пароли, платёжные реквизиты, приватные URL.

## 26. Инфраструктура

Локальное окружение поднимается одной документированной командой. Docker Compose включает: PostgreSQL, Redis, MinIO, FastAPI, Celery workers, Celery Beat, Next.js, Go promo service, ClickHouse (при использовании), observability stack или облегчённый профиль мониторинга, mail testing service при необходимости.

Подготовить: `.env.example`, dev/test/staging профили, production configuration template, GitHub Actions, Alembic migrations, seed script, backups, restore guide, Terraform skeleton, Kubernetes templates, readiness/liveness probes. Все контейнеры — с health checks.

## 27. Тестирование

Уровни: unit, integration, API contract, end-to-end, migration, security, smoke, load, concurrency, payment idempotency.

Обязательные E2E-сценарии:
1. OAuth → refresh rotation → logout.
2. Генерация текста → аудио → отправка в Офис.
3. Multipart upload → потеря сети → возобновление.
4. Релиз → валидация → скоринг.
5. Кворк → заказ → hold → выполнение → capture.
6. Спор → частичный refund.
7. Повтор платёжного webhook без двойного списания.
8. Запрет доступа к чужому S3-файлу.
9. Чат между двумя backend-инстансами через Redis.
10. Восстановление WebSocket после потери сети.
11. Запрет недопустимого state transition.
12. Отсутствие зависимости основного API от сбоя внешнего AI-провайдера.
13. Отсутствие зависимости каталога и Маркета от Go-сервиса.
14. Работа mock-режима без API-ключей.

## 28. Целевые показатели производительности

10 000 MAU, 1 000 одновременных WebSocket-соединений, 100 RPS продолжительной нагрузки, пики до 300 RPS, media assets до 5 ГБ, 100 одновременных фоновых аудиозадач, горизонтальное масштабирование API и workers. Без преждевременной оптимизации, но без архитектурных блокировок этих показателей.

## 29. Правила качества кода

Строгая типизация; никакого `any` без документированного исключения; не подавлять ошибки линтера без причины; никаких пустых catch-блоков; никаких секретов в репозитории; никакой фиктивной безопасности; никакого float для денег; никаких глобальных mutable singletons; не дублировать доменную логику во frontend; не доверять данным клиента; UI-проверка не заменяет backend authorization; никаких неиспользуемых абстракций; никаких критических TODO; mock-интеграция никогда не выдаётся за production.

Каждый допустимый TODO: имеет идентификатор, записан в `KNOWN_LIMITATIONS.md`, имеет приоритет, имеет условие закрытия, не блокирует acceptance criteria MVP.

## 30. Этапы реализации

**Этап 0. Анализ и архитектура** — анализ требований, конфликтная матрица, version matrix, C4, ER, ADR, threat model, implementation plan, acceptance matrix.

**Этап 1. Монорепозиторий и инфраструктура** — workspace, Docker Compose, PostgreSQL, Redis, MinIO, базовый CI, linters, formatters, health checks.

**Этап 2. Backend foundation** — FastAPI, config, DB, migrations, errors, logging, auth foundation, audit, provider interfaces.

**Этап 3. Авторизация** — OAuth, JWT, refresh rotation, RBAC, sessions, тесты.

**Этап 4. ИТ-Студия** — lyricist, rhythm, rhymes, versions, assistant, audio jobs, SSE, mock providers, web UI.

**Этап 5. Media и Офис** — media assets, multipart upload, validation, projects, releases, scoring, distribution mock.

**Этап 6. Маркет и Billing** — kworks, profiles, orders, ledger, escrow mock, chat, disputes, admin flow.

**Этап 7. Лента и Community** — CMS, feed, chart adapters, Redis cache, rooms, WebSockets, horizontal test.

**Этап 8. Legal Promotion Service** — Go service, campaigns, budgets, analytics, ClickHouse, internal promo feedback.

**Этап 9. Flutter** — app foundation, auth, feed, projects, jobs, player, chat.

**Этап 10. Hardening** — observability, security headers, rate limits, file scanning, failure isolation, backups, deployment templates.

**Этап 11. Acceptance** — full test suite, E2E, load tests, security checks, production builds, documentation audit, acceptance matrix, финальный отчёт.

## 31. Протокол выполнения (обязателен для каждой сессии)

1. Изучи весь доступный контекст.
2. Проверь текущее состояние репозитория.
3. Не удаляй существующий рабочий код без необходимости.
4. Создай/обнови implementation plan.
5. Реализуй только текущий этап.
6. Запусти проверки.
7. Исправь ошибки.
8. Обнови документацию.
9. Напиши краткий отчёт (формат ниже).
10. Переходи к следующему этапу, если позволяет лимит контекста.
11. Перед завершением сессии обязательно обнови `IMPLEMENTATION_STATE.md`.

## 32. Формат отчёта после каждого этапа

```
Этап:
Статус:

Реализовано:
- ...

Измененные компоненты:
- ...

Миграции:
- ...

API:
- ...

Проверки:
- command: result

Тесты:
- passed:
- failed:
- skipped:

Mock-интеграции:
- ...

Известные ограничения:
- ...

Следующий этап:
- ...
```

## 33. Definition of Done

Проект НЕ считается готовым, пока:
- Docker Compose не запускается;
- миграции не применяются;
- seed-данные не создаются;
- web production build не проходит;
- backend tests не проходят;
- frontend type-check не проходит;
- Flutter analyze не проходит;
- Go tests не проходят;
- критические E2E не проходят;
- OpenAPI не генерируется;
- чужие S3-файлы доступны;
- платёжные webhooks могут примениться дважды;
- state machines допускают незаконные переходы;
- основные потоки существуют только визуально;
- документация запуска неполна;
- mock-функции не обозначены явно;
- acceptance matrix не заполнена.

## 34. Финальные артефакты

Полный исходный код; `.env.example`; Docker Compose; lock-файлы; миграции; seed-данные; тестовые аккаунты; mock providers; OpenAPI; ER-диаграмма; C4-диаграммы; ADR; threat model; README; local setup guide; deployment guide; backup/restore guide; security checklist; acceptance checklist; API documentation; тестовый отчёт; отчёт о нагрузке; перечень mock-функций; перечень отложенных production-интеграций; финальный отчёт о реализованных требованиях.

---

**Начни с Этапа 0.** Изучи приложенные Master-ТЗ и документ зафиксированных решений, построй конфликтную матрицу (приоритет — зафиксированные решения), зафиксируй версии стека, создай `docs/IMPLEMENTATION_PLAN.md` и переходи к реализации по протоколу из раздела 31.
