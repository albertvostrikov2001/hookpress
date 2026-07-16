"""SSRF guard regression tests."""

import pytest

from app.core.errors import AppError
from app.infrastructure.security.ssrf import validate_public_url

pytestmark = pytest.mark.security


def test_blocks_localhost():
    with pytest.raises(AppError) as exc:
        validate_public_url("http://localhost/feed.xml")
    assert exc.value.code == "ssrf_blocked"


def test_blocks_private_ip_literal():
    with pytest.raises(AppError) as exc:
        validate_public_url("http://127.0.0.1/feed.xml")
    assert exc.value.code == "ssrf_blocked"


def test_rejects_non_http_scheme():
    with pytest.raises(AppError) as exc:
        validate_public_url("file:///etc/passwd")
    assert exc.value.code == "invalid_url"


def test_allows_public_https():
    validate_public_url("https://example.com/rss.xml")
