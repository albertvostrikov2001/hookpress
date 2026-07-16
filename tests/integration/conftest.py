"""Integration test fixtures."""

import os
import socket
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
API_ROOT = REPO_ROOT / "services" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

# Host-side runs: map docker-compose service hostnames to localhost.
_LOCAL_DEFAULTS = {
    "REDIS_URL": "redis://localhost:6379/0",
    "DATABASE_URL": "postgresql+asyncpg://hookpress:hookpress_dev@localhost:5432/hookpress",
}
for key, local_default in _LOCAL_DEFAULTS.items():
    current = os.environ.get(key, local_default)
    if "://redis:" in current or "@postgres:" in current:
        os.environ[key] = local_default
    else:
        os.environ.setdefault(key, local_default)

os.environ.setdefault("RATE_LIMIT_ENABLED", "false")


def _port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@pytest.fixture(scope="session")
def redis_available() -> bool:
    return _port_open("localhost", 6379)


@pytest.fixture(scope="session")
def postgres_available() -> bool:
    return _port_open("localhost", 5432)


@pytest.fixture
def require_redis(redis_available):
    if not redis_available:
        pytest.skip("Redis not reachable on localhost:6379")


@pytest.fixture
def require_postgres(postgres_available):
    if not postgres_available:
        pytest.skip("PostgreSQL not reachable on localhost:5432")
