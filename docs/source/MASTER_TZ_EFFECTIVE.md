# Master-ТЗ (Effective — synthesized from master prompt)

> Original Master-ТЗ attachment was not provided. Requirements below mirror master prompt **§7–§22** as the effective product specification.

## Platform domains

auth, users, studio, media, office, releases, scoring, distribution, market, billing, disputes, chat, community, media_feed, charts, promotions, notifications, admin, audit.

## Auth (§8)

OAuth 2.0: Google, Yandex, VK; Apple-ready. JWT RS256. Refresh rotation + reuse detection. RBAC + scopes. Dev-login for local dev.

## IT Studio (§9)

End-to-end: lyrics → edit → rhythm → rhymes → assistant → audio demo → progress → listen → send to Office. Theme/mood/genre/structure, lyric versions, syllables, rhyme map, two-panel editor, fragment edits, Celery audio, SSE + polling, waveform, mock LLM/audio adapters.

## Office (§10)

Singles/EP/albums, tracks, metadata, contributors, explicit, release dates, multipart resumable upload, WAV/cover validation, scoring jobs, mock distribution, test UPC/ISRC, idempotent send-to-office.

## Scoring (§11)

LibROSA heuristics in Celery: BPM, key, spectral centroid, dynamic range, intro duration, loudness, genre ranges, advisory score, confidence, reasons, recommendations, limitations.

## Distribution (§12)

DistributionProvider + mock: metadata package, delivery status, retry, idempotent webhooks, DDEX adapter interface stub.

## Market (§13)

Kwork categories (design, production, sound, songwriting), profiles, search/filters/rating/portfolio, orders, spec versions, deal chat, files, delivery, revisions, acceptance, disputes, moderator UI.

## Billing (§14)

Double-entry ledger, integer minor units, idempotent operations, escrow hold/capture/refund, platform commission, mock PaymentProvider.

## Disputes (§15)

Open, freeze order, immutable messages, evidence, moderator resolution, partial refund/payout, audit.

## Feed (§16)

CMS: articles, categories, tags, authors, drafts, publish, RSS ingest, moderation, pagination, likes, bookmarks, views, comments, SEO.

## Charts (§17)

Source interface, weights, position history, dynamics, Redis cache, background updates, mock sources with labels, admin weight config.

## Chat (§18)

Rooms, WS + Redis pub/sub, presence, typing, read status, reconnect backoff, client message dedup, optimistic UI, attachments, horizontal scale test.

## Promo (§19)

Go service: campaigns, budgets, schedule, internal placements, events → ClickHouse, stats API, voluntary listening, ratings, internal antifraud.

## Media (§20)

Private S3, presigned URLs, multipart, MIME/size/checksum, AV quarantine states, lifecycle cleanup, immutable versions.

## Web (§21)

Next.js App Router, i18n ru/en, dark/light, WCAG 2.1 AA, SEO, all screens API-connected.

## Mobile (§22)

Flutter: auth, feed, projects, jobs, player, waveform, chat reconnect, offline-tolerant chat/tasks, i18n. iOS 16+, Android 10+.

## State machines (§23)

Enforced on backend for AI Task, Office Project, Release, Market Order, Payment, Dispute — see master prompt §23 diagram.
