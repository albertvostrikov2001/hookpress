# Run E2E against Docker API (avoids Windows proxy on localhost:8000)
$ErrorActionPreference = "Stop"
$env:HOOKPRESS_API_URL = "http://127.0.0.1:8000"
$env:HOOKPRESS_BUYER_EMAIL = "admin@example.com"
py -3.12 -m pip install -q -r tests/e2e/requirements.txt
py -3.12 -m pytest tests/e2e -m e2e -q
