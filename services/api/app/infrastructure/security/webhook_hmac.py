"""Webhook HMAC verification."""

import hashlib
import hmac


def compute_hmac_signature(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def verify_hmac_signature(secret: str, body: bytes, signature: str) -> bool:
    if not signature:
        return False
    expected = compute_hmac_signature(secret, body)
    return hmac.compare_digest(expected, signature.strip())
