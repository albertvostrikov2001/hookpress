"""Alembic migration smoke test — upgrade head against running Postgres."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
API_ROOT = REPO_ROOT / "services" / "api"


def _database_reachable() -> bool:
    url = os.getenv("DATABASE_URL", "postgresql+asyncpg://hookpress:hookpress_dev@localhost:5432/hookpress")
    if "localhost" not in url and "127.0.0.1" not in url:
        return True
    try:
        import socket

        sock = socket.create_connection(("localhost", 5432), timeout=2)
        sock.close()
        return True
    except OSError:
        return False


@pytest.mark.integration
def test_alembic_upgrade_head():
    if not _database_reachable():
        pytest.skip("PostgreSQL not reachable on localhost:5432")

    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(API_ROOT))
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=API_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr or result.stdout
