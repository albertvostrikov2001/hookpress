"""Apple OAuth provider stub tests."""

import pytest

from app.core.errors import AppError
from app.infrastructure.providers.oauth import AppleOAuthProvider, get_oauth_provider


def test_apple_provider_not_configured_by_default():
    provider = AppleOAuthProvider()
    assert provider.is_configured() is False


def test_get_apple_provider_raises_when_unconfigured():
    with pytest.raises(AppError) as exc:
        get_oauth_provider("apple")
    assert exc.value.status_code == 501


@pytest.mark.asyncio
async def test_apple_authorization_url_when_configured(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "oauth_apple_client_id", "com.hookpress.app")
    monkeypatch.setattr(settings, "oauth_apple_team_id", "TEAM123")
    provider = AppleOAuthProvider()
    url = await provider.get_authorization_url(state="s", redirect_uri="http://localhost/cb")
    assert "appleid.apple.com" in url
    assert "state=s" in url
