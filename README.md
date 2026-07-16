# hook.press

Production-ready MVP monorepo for the hook.press music platform: IT Studio, Office, Market, Community, and legal promotion.

## Quick Start

```powershell
copy .env.example .env
docker compose up -d --build
docker exec -w /app hookpress-api-1 alembic upgrade head
docker exec -w /app -e PYTHONPATH=/app hookpress-api-1 python scripts/seed.py

# Verify
.\scripts\e2e.ps1
docker exec -w /app hookpress-api-1 sh -c "PYTHONPATH=/app pytest -q"
```

| Service | URL |
|---------|-----|
| Web | http://localhost:3000 |
| API | http://localhost:8000/health |
| API docs | http://localhost:8000/api/v1/docs |
| MinIO Console | http://localhost:9001 |
| Grafana (monitoring profile) | http://localhost:3001 |
| Jaeger UI (tracing) | http://localhost:16686 |

### Monitoring profile

Prometheus and Grafana are optional. Enable with:

```powershell
docker compose --profile monitoring up -d
```

OpenTelemetry traces export to Jaeger by default (`OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317`).

Load tests (k6): see [tests/load/README.md](tests/load/README.md).

## Repository Structure

```
apps/web          Next.js web application
apps/mobile       Flutter mobile app
services/api      FastAPI modular monolith
services/promo    Go legal promotion service
workers/celery    Celery background workers
packages/         Shared TS packages
infra/docker      Docker & compose configs
docs/             Architecture & state docs
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Implementation State](docs/IMPLEMENTATION_STATE.md) — **start here between sessions**
- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Deploy from GitHub (Render)](docs/DEPLOY_GITHUB.md)
- [API](docs/API.md)
- [Security](docs/SECURITY.md)

## Development Without API Keys

All external integrations use mock providers by default. See [Known Limitations](docs/KNOWN_LIMITATIONS.md).

## License

Proprietary — hook.press
