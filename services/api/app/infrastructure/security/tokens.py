"""Token hashing utilities."""

import hashlib
import secrets

from app.core.config import settings


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    material = f"{settings.api_secret_key}:{token}".encode()
    return hashlib.sha256(material).hexdigest()
