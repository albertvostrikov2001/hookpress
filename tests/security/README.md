# Security tests

SSRF, IDOR, auth bypass smoke tests.

Requires API dependencies (install from `services/api/requirements.txt`).

```bash
PYTHONPATH=services/api pytest tests/security -q
```
