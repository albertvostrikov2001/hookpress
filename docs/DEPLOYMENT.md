# Deployment Guide

## Local Development (primary)

```powershell
# Clone and configure
cp .env.example .env

# Start stack
docker compose up -d --build

# Verify
docker compose ps
curl http://localhost:8000/health
curl http://localhost:3000
```

Default ports:
| Service | Port |
|---------|------|
| Web (Next.js) | 3000 |
| API (FastAPI) | 8000 |
| Promo (Go) | 8081 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| MinIO API | 9000 |
| MinIO Console | 9001 |
| ClickHouse HTTP | 8123 |
| Prometheus | 9090 |
| Grafana | 3001 |

## Environment Profiles

| Profile | File | Use |
|---------|------|-----|
| dev | `.env` | Local docker compose |
| test | `.env.test` | CI integration tests |
| staging | `infra/docker/.env.staging.template` | Pre-prod template |
| production | `infra/docker/.env.production.template` | Prod template (no secrets committed) |

## Docker Compose Services

- `postgres` — primary database
- `redis` — broker, cache, pub/sub
- `minio` — S3-compatible storage
- `api` — FastAPI
- `celery-worker` — background jobs
- `celery-beat` — scheduled tasks
- `web` — Next.js
- `promo` — Go legal promotion service
- `clickhouse` — analytics (promo)
- `mailhog` — email testing (optional profile)
- `prometheus` + `grafana` — monitoring (optional profile)

Profiles:
- `default` — core MVP services
- `monitoring` — adds prometheus/grafana
- `mail` — adds mailhog

## Production Checklist (template)

1. Provision PostgreSQL 16 (managed), Redis 7, S3 (or MinIO cluster), ClickHouse
2. Mount JWT RS256 private key via secret manager
3. Configure OAuth client IDs/secrets for Google, Yandex, VK
4. Set `CORS_ORIGINS`, `COOKIE_DOMAIN`, `TLS` at ingress
5. Run `alembic upgrade head` as init job
6. Enable Sentry DSN, OTel exporter endpoint
7. Configure backup: PG daily, MinIO versioning/lifecycle
8. Horizontal scale: API (stateless), Celery workers, WS with Redis adapter

## Kubernetes

Skeleton manifests in `infra/kubernetes/`:
- Deployments: api, web, celery-worker, promo
- Services + Ingress
- ConfigMaps / ExternalSecrets
- Liveness/readiness probes on `/health`, `/ready`

## Terraform

Skeleton in `infra/terraform/` for future cloud provisioning (modules stubbed).

## Backup & Restore

### PostgreSQL
```bash
docker compose exec postgres pg_dump -U hookpress hookpress > backup.sql
docker compose exec -T postgres psql -U hookpress hookpress < backup.sql
```

### MinIO
Use `mc mirror` against bucket `hookpress-media`.

## GitHub Actions

Workflow `.github/workflows/ci.yml`:
- Lint/format all languages
- Unit tests
- Docker build smoke
- Migration dry-run against ephemeral PG

## Rollback

1. Redeploy previous image tag
2. Run down migration only if explicitly tested (prefer forward-fix)
3. Rotate secrets if compromise suspected
