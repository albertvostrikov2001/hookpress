# Deploy hook.press from GitHub

Public demo URL (after Render setup): **https://hookpress-web.onrender.com**  
Repository: **https://github.com/albertvostrikov2001/hookpress**

GitHub Pages cannot run the full stack (PostgreSQL, Redis, FastAPI, WebSockets). Use **Render Blueprint** connected to this repo for a working public site.

## 1. Push code to GitHub

```powershell
cd C:\Work\Hook.press
git init
git branch -M main
git remote add origin https://github.com/albertvostrikov2001/hookpress.git
git add .
git commit -m "Initial hook.press MVP — web, API, docs, Render blueprint"
git push -u origin main
```

If the remote already has commits, use `git pull origin main --rebase` first, then push.

## 2. Redis (required for chat & rate limits)

1. Create a free database at [Upstash Redis](https://upstash.com/)
2. Copy the **Redis URL** (`rediss://...`)

## 3. Deploy on Render (from GitHub)

1. Open [Render Dashboard → Blueprints](https://dashboard.render.com/blueprints)
2. **New Blueprint Instance** → connect `albertvostrikov2001/hookpress`
3. Apply `render.yaml` (creates Postgres + API + Web)
4. In **hookpress-api** → Environment:
   - `REDIS_URL` = your Upstash URL
   - `CORS_ORIGINS` = `https://hookpress-web.onrender.com` (use your actual web URL after deploy)
5. Optional S3 (media uploads): set `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY` (e.g. Cloudflare R2)
6. Wait for deploy; API runs migrations + seed on start

## 4. Verify

| Check | URL |
|-------|-----|
| Web | `https://<hookpress-web>.onrender.com` |
| API health | `https://<hookpress-api>.onrender.com/health` |
| API docs | `https://<hookpress-api>.onrender.com/api/v1/docs` |

Dev login: `artist@example.com`, `admin@example.com` (no password).

## 5. GitHub Actions (CI)

On every push to `main`, CI runs:

- API: ruff + pytest
- Web: typecheck + build
- Promo (Go), Flutter analyze
- E2E (Postgres + Redis services)

See `.github/workflows/ci.yml`.

## 6. Local development (unchanged)

```powershell
docker compose up -d --build
docker exec -w /app hookpress-api-1 alembic upgrade head
docker exec -w /app -e PYTHONPATH=/app hookpress-api-1 python scripts/seed.py
```

Web: http://localhost:3000 · API: http://localhost:8000

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Web empty / API errors | Set `CORS_ORIGINS` on API to exact web URL |
| Chat / WS fails | Ensure `REDIS_URL` is set; use `wss://` via CSP (auto from API URL) |
| 401 on all pages | Re-login at `/ru/login` (tokens expire; refresh cookie needs same-site HTTPS) |
| Media upload fails | Configure S3-compatible storage env vars on API |

## Notes

- Render **free** tier sleeps after inactivity (~50s cold start on first visit).
- JWT keys are generated inside the API container on first boot (`certs/dev/`).
- Do not commit `.env` — use Render/Upstash dashboards for secrets.
