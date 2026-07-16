"""JWT RS256 helpers."""

import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core.config import settings
from app.core.errors import AppError
from app.domain.auth.roles import Role

_private_key: str | None = None
_public_key: str | None = None


def _ensure_dev_keys() -> None:
    private_path = Path(settings.jwt_private_key_path)
    public_path = Path(settings.jwt_public_key_path)
    if private_path.exists() and public_path.exists():
        return
    if settings.is_production:
        raise RuntimeError("JWT keys missing in production")
    private_path.parent.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    private_path.write_bytes(private_pem)
    public_path.write_bytes(public_pem)


def _load_keys() -> tuple[str, str]:
    global _private_key, _public_key
    if _private_key and _public_key:
        return _private_key, _public_key
    _ensure_dev_keys()
    _private_key = Path(settings.jwt_private_key_path).read_text(encoding="utf-8")
    _public_key = Path(settings.jwt_public_key_path).read_text(encoding="utf-8")
    return _private_key, _public_key


def create_access_token(
    *, user_id: uuid.UUID, email: str, roles: list[str], scopes: list[str] | None = None
) -> str:
    private_key, _ = _load_keys()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "email": email,
        "roles": roles,
        "scopes": scopes or [],
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_ttl_minutes),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


def decode_access_token(token: str) -> dict:
    _, public_key = _load_keys()
    try:
        payload = jwt.decode(token, public_key, algorithms=["RS256"], options={"require": ["exp", "sub"]})
    except jwt.PyJWTError as exc:
        raise AppError("invalid_token", "Invalid or expired access token", status_code=401) from exc
    if payload.get("type") != "access":
        raise AppError("invalid_token", "Invalid token type", status_code=401)
    return payload


def roles_from_payload(payload: dict) -> set[Role]:
    raw = payload.get("roles") or []
    return {Role(r) for r in raw if r in Role._value2member_map_}
