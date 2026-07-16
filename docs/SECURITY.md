# Security — Threat Model & Controls

## Scope

hook.press MVP: auth, payments (mock), file access, marketplace, chat, webhooks, AI provider integrations.

## Assets

- User PII (email, profile, OAuth tokens)
- JWT refresh tokens & session records
- Media assets (audio, covers) in private S3
- Financial ledger (escrow balances)
- Chat messages & marketplace order data
- Admin/mod audit logs

## Threat Model Summary

### Auth (STRIDE)

| Threat | Impact | Mitigation |
|--------|--------|------------|
| Token theft (XSS) | Account takeover | HttpOnly Secure cookies (web); short-lived access JWT; CSP |
| Refresh token reuse | Session hijack | Rotation + reuse detection → revoke all sessions |
| OAuth CSRF | Wrong account link | state parameter, redirect URI allowlist |
| Brute force login | Credential stuffing | Rate limiting, lockout backoff |
| Privilege escalation | Unauthorized admin | RBAC server-side; admin role admin-only assignment |

### Payments

| Threat | Impact | Mitigation |
|--------|--------|------------|
| Webhook replay | Double charge | Idempotency keys, unique external txn IDs, signature validation |
| Race on ledger | Incorrect balance | Row locking, serializable transactions for balance updates |
| Amount tampering | Financial loss | Integer minor units only; server-side price validation |
| Client-side price trust | Underpayment | Never trust client amounts for kwork orders |

### File Access

| Threat | Impact | Mitigation |
|--------|--------|------------|
| IDOR on presigned URLs | Data leak | AuthZ check before URL mint; short TTL; object key non-guessable |
| Malware upload | Platform abuse | MIME sniff, size limits, quarantine scan state |
| Public bucket misconfig | Mass leak | Private buckets only; test denies cross-user access |

### Marketplace

| Threat | Impact | Mitigation |
|--------|--------|------------|
| Order state manipulation | Free work / unpaid delivery | Backend state machine guards |
| Dispute message tampering | Evidence loss | Immutable messages after dispute open |
| Fake reviews | Trust erosion | Order-completed-only reviews (future hardening) |

### Chat

| Threat | Impact | Mitigation |
|--------|--------|------------|
| WS auth bypass | Eavesdropping/spam | JWT on connect; room membership checks |
| Message injection | XSS | Output encoding; content sanitization |
| Flooding | DoS | Rate limits per user/room |

### Webhooks (distribution, payments)

| Threat | Impact | Mitigation |
|--------|--------|------------|
| Forged webhook | State corruption | HMAC signature + timestamp replay window |
| Duplicate delivery | Double processing | Idempotency store |

### AI Integrations

| Threat | Impact | Mitigation |
|--------|--------|------------|
| Prompt injection to backend | Data exfil | Separate user content boundaries; no tool exec from lyrics |
| API key leak | Cost/abuse | Env secrets only; never log prompts with keys |
| Provider outage | DoS | Mock fallback; async jobs isolated from API availability |

## Security Controls Checklist

- [x] TLS termination configurable (reverse proxy / ingress)
- [x] JWT RS256 with secure key storage
- [x] Refresh rotation + reuse detection
- [x] CORS allowlist per environment
- [x] CSP headers (web)
- [x] CSRF protection for cookie-based flows
- [x] Rate limiting (API gateway / middleware)
- [x] Input validation (Pydantic + Zod)
- [x] SQL parameterized queries (SQLAlchemy)
- [x] SSRF guards on outbound URL fetch (feed ingest)
- [x] Secrets via env / secret manager only
- [x] No secrets in logs or telemetry
- [ ] Dependency scanning in CI
- [x] Security headers (HSTS, X-Frame-Options, etc.)
- [x] Audit log for admin/financial actions

## Data Classification

| Class | Examples | Handling |
|-------|----------|----------|
| Public | Published articles, public profiles | Cacheable |
| Internal | Aggregated metrics | Authenticated staff |
| Confidential | PII, ledger, private media | Encrypted transit; access logged |
| Restricted | JWT keys, PSP credentials | Secret manager only |

## Incident Response (MVP)

1. Revoke compromised refresh tokens (session table flag).
2. Rotate JWT signing keys (forces re-login).
3. Invalidate presigned URLs (TTL expiry + key rotation on bucket policy if needed).
4. Freeze disputed orders automatically on dispute open.

## Compliance Notes

- Real KYC/AML and production payouts out of MVP scope — see `KNOWN_LIMITATIONS.md`.
- Test UPC/ISRC clearly labeled non-official.
- Promo analytics must not claim external DSP manipulation.
