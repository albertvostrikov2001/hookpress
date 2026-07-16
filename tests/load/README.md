# Load tests

k6 scripts for performance targets (master prompt §28).

| Script | Target |
|--------|--------|
| `api_sustained.js` | 100 RPS sustained, 5 min |
| `api_spike.js` | 300 RPS spike |
| `ws_connections.js` | 1000 concurrent WebSocket connections |

Run:

```bash
k6 run tests/load/api_sustained.js
```

Requires [k6](https://k6.io/) installed.
