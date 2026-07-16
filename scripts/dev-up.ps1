# PowerShell helper — start local stack
Copy-Item -Path .env.example -Destination .env -Force -ErrorAction SilentlyContinue
docker compose up -d --build
docker compose ps
