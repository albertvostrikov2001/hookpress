# Integration tests

Cross-service tests requiring PostgreSQL, Redis, or multiple API instances.

Run (stack must be up):

```bash
pytest tests/integration -q
```

## Multi-instance chat

The test `test_chat_redis.py` validates Redis pub/sub relay used for
horizontal chat scaling. For full end-to-end WebSocket verification across
process boundaries, scale the API service:

```bash
docker compose up -d --scale api=2
export HOOKPRESS_MULTI_API=1   # Windows: set HOOKPRESS_MULTI_API=1
pytest tests/integration/test_chat_redis.py -q
```

With a **single API instance**, `test_two_subscribers_receive_same_message` still
runs; `test_chat_service_subscribe_across_instances` is skipped unless
`HOOKPRESS_MULTI_API=1`.

## Migrations

```bash
pytest tests/integration/test_migrations.py -q
```

Requires PostgreSQL reachable (docker compose postgres on :5432).
