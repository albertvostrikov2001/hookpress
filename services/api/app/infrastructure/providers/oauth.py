"""OAuth provider interfaces and implementations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from app.core.config import settings
from app.core.errors import AppError


@dataclass(frozen=True)
class OAuthUserInfo:
    subject: str
    email: str
    display_name: str


class OAuthProvider(ABC):
    name: str

    @abstractmethod
    def is_configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_authorization_url(self, *, state: str, redirect_uri: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def exchange_code(self, *, code: str, redirect_uri: str) -> OAuthUserInfo:
        raise NotImplementedError


class MockOAuthProvider(OAuthProvider):
    """Deterministic OAuth provider for development and tests."""

    name = "mock"

    def is_configured(self) -> bool:
        return True

    async def get_authorization_url(self, *, state: str, redirect_uri: str) -> str:
        params = urlencode({"state": state, "redirect_uri": redirect_uri, "provider": self.name})
        return f"http://mock-oauth.test/authorize?{params}"

    async def exchange_code(self, *, code: str, redirect_uri: str) -> OAuthUserInfo:
        if code.startswith("mock:"):
            parts = code.split(":", 3)
            if len(parts) < 3:
                raise AppError("invalid_oauth_code", "Invalid mock OAuth code", status_code=400)
            email = parts[1]
            display_name = parts[2] if len(parts) > 2 else email.split("@")[0]
            subject = parts[3] if len(parts) > 3 else f"mock-{email}"
            return OAuthUserInfo(subject=subject, email=email, display_name=display_name)
        return OAuthUserInfo(
            subject=f"mock-{code}",
            email="oauth-mock@example.com",
            display_name="OAuth Mock User",
        )


class GoogleOAuthProvider(OAuthProvider):
    name = "google"

    def is_configured(self) -> bool:
        return bool(settings.oauth_google_client_id and settings.oauth_google_client_secret)

    async def get_authorization_url(self, *, state: str, redirect_uri: str) -> str:
        params = urlencode(
            {
                "client_id": settings.oauth_google_client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "access_type": "online",
                "prompt": "select_account",
            }
        )
        return f"https://accounts.google.com/o/oauth2/v2/auth?{params}"

    async def exchange_code(self, *, code: str, redirect_uri: str) -> OAuthUserInfo:
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.oauth_google_client_id,
                    "client_secret": settings.oauth_google_client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            if token_resp.status_code != 200:
                raise AppError("oauth_exchange_failed", "Google token exchange failed", status_code=502)
            access_token = token_resp.json()["access_token"]

            user_resp = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if user_resp.status_code != 200:
                raise AppError("oauth_userinfo_failed", "Google userinfo request failed", status_code=502)
            data = user_resp.json()
            return OAuthUserInfo(
                subject=data["sub"],
                email=data["email"],
                display_name=data.get("name") or data["email"].split("@")[0],
            )


class YandexOAuthProvider(OAuthProvider):
    name = "yandex"

    def is_configured(self) -> bool:
        return bool(settings.oauth_yandex_client_id and settings.oauth_yandex_client_secret)

    async def get_authorization_url(self, *, state: str, redirect_uri: str) -> str:
        params = urlencode(
            {
                "client_id": settings.oauth_yandex_client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "state": state,
            }
        )
        return f"https://oauth.yandex.ru/authorize?{params}"

    async def exchange_code(self, *, code: str, redirect_uri: str) -> OAuthUserInfo:
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_resp = await client.post(
                "https://oauth.yandex.ru/token",
                data={
                    "code": code,
                    "client_id": settings.oauth_yandex_client_id,
                    "client_secret": settings.oauth_yandex_client_secret,
                    "grant_type": "authorization_code",
                },
            )
            if token_resp.status_code != 200:
                raise AppError("oauth_exchange_failed", "Yandex token exchange failed", status_code=502)
            access_token = token_resp.json()["access_token"]

            user_resp = await client.get(
                "https://login.yandex.ru/info",
                params={"format": "json"},
                headers={"Authorization": f"OAuth {access_token}"},
            )
            if user_resp.status_code != 200:
                raise AppError("oauth_userinfo_failed", "Yandex userinfo request failed", status_code=502)
            data = user_resp.json()
            email = data.get("default_email") or f"{data['id']}@yandex.oauth"
            return OAuthUserInfo(
                subject=str(data["id"]),
                email=email,
                display_name=data.get("display_name") or data.get("real_name") or email.split("@")[0],
            )


class VkOAuthProvider(OAuthProvider):
    name = "vk"

    def is_configured(self) -> bool:
        return bool(settings.oauth_vk_client_id and settings.oauth_vk_client_secret)

    async def get_authorization_url(self, *, state: str, redirect_uri: str) -> str:
        params = urlencode(
            {
                "client_id": settings.oauth_vk_client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "email",
                "state": state,
                "v": "5.131",
            }
        )
        return f"https://oauth.vk.com/authorize?{params}"

    async def exchange_code(self, *, code: str, redirect_uri: str) -> OAuthUserInfo:
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_resp = await client.get(
                "https://oauth.vk.com/access_token",
                params={
                    "code": code,
                    "client_id": settings.oauth_vk_client_id,
                    "client_secret": settings.oauth_vk_client_secret,
                    "redirect_uri": redirect_uri,
                },
            )
            if token_resp.status_code != 200:
                raise AppError("oauth_exchange_failed", "VK token exchange failed", status_code=502)
            data = token_resp.json()
            if "error" in data:
                raise AppError("oauth_exchange_failed", data.get("error_description", "VK token exchange failed"), status_code=502)
            user_id = str(data["user_id"])
            email = data.get("email") or f"{user_id}@vk.oauth"

            profile_resp = await client.get(
                "https://api.vk.com/method/users.get",
                params={
                    "user_ids": user_id,
                    "fields": "screen_name",
                    "access_token": data["access_token"],
                    "v": "5.131",
                },
            )
            display_name = email.split("@")[0]
            if profile_resp.status_code == 200:
                profile = profile_resp.json()
                items = profile.get("response") or []
                if items:
                    first = items[0]
                    display_name = f"{first.get('first_name', '')} {first.get('last_name', '')}".strip() or display_name

            return OAuthUserInfo(subject=user_id, email=email, display_name=display_name)


class AppleOAuthProvider(OAuthProvider):
    """Apple Sign-In stub — interface ready for production keys (TODO-004)."""

    name = "apple"

    def is_configured(self) -> bool:
        return bool(settings.oauth_apple_client_id and settings.oauth_apple_team_id)

    async def get_authorization_url(self, *, state: str, redirect_uri: str) -> str:
        params = urlencode(
            {
                "client_id": settings.oauth_apple_client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "response_mode": "form_post",
                "scope": "name email",
                "state": state,
            }
        )
        return f"https://appleid.apple.com/auth/authorize?{params}"

    async def exchange_code(self, *, code: str, redirect_uri: str) -> OAuthUserInfo:
        raise AppError(
            "oauth_not_configured",
            "Apple Sign-In requires production keys. Use dev-login locally.",
            status_code=501,
            details={"provider": self.name},
        )


_PROVIDERS: dict[str, type[OAuthProvider]] = {
    "mock": MockOAuthProvider,
    "google": GoogleOAuthProvider,
    "yandex": YandexOAuthProvider,
    "vk": VkOAuthProvider,
    "apple": AppleOAuthProvider,
}


def get_oauth_provider(name: str) -> OAuthProvider:
    cls = _PROVIDERS.get(name.lower())
    if cls is None:
        raise AppError(
            "oauth_provider_unknown",
            f"Unknown OAuth provider '{name}'",
            status_code=400,
            details={"provider": name},
        )
    provider = cls()
    if not provider.is_configured():
        raise AppError(
            "oauth_not_configured",
            f"OAuth provider '{name}' is not configured. Use dev-login locally.",
            status_code=501,
            details={"provider": name, "mock": name == "mock"},
        )
    return provider


def oauth_redirect_uri(provider: str) -> str:
    mapping = {
        "mock": settings.oauth_mock_redirect_uri,
        "google": settings.oauth_google_redirect_uri,
        "yandex": settings.oauth_yandex_redirect_uri,
        "vk": settings.oauth_vk_redirect_uri,
        "apple": settings.oauth_apple_redirect_uri,
    }
    uri = mapping.get(provider.lower())
    if not uri:
        raise AppError(
            "oauth_provider_unknown",
            f"Unknown OAuth provider '{provider}'",
            status_code=400,
            details={"provider": provider},
        )
    return uri
