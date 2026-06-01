"""
Symmetric encryption helpers for user-supplied AI API keys.

In production set ``AI_KEY_FERNET_KEY`` (a 32-byte url-safe base64 value
generated via ``Fernet.generate_key()``) in the environment. For local
development we derive a stable key from ``SECRET_KEY`` so the app boots
without extra setup -- this is NOT safe for production rotation.
"""
import base64
import hashlib

from django.conf import settings

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover - dependency missing in dev
    Fernet = None
    InvalidToken = Exception


_FERNET_INSTANCE = None


def _get_fernet():
    global _FERNET_INSTANCE
    if _FERNET_INSTANCE is not None:
        return _FERNET_INSTANCE

    if Fernet is None:
        raise RuntimeError(
            "cryptography is not installed. Add 'cryptography>=42' to requirements.txt"
        )

    key = getattr(settings, "AI_KEY_FERNET_KEY", "") or ""
    if not key:
        # Dev fallback: derive a deterministic 32-byte key from SECRET_KEY.
        digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
        key = base64.urlsafe_b64encode(digest)
    elif isinstance(key, str):
        key = key.encode("utf-8")

    _FERNET_INSTANCE = Fernet(key)
    return _FERNET_INSTANCE


def encrypt(plaintext: str) -> bytes:
    if plaintext is None:
        raise ValueError("plaintext required")
    return _get_fernet().encrypt(plaintext.encode("utf-8"))


def decrypt(ciphertext) -> str:
    if not ciphertext:
        return ""
    if isinstance(ciphertext, memoryview):
        ciphertext = bytes(ciphertext)
    if isinstance(ciphertext, str):
        ciphertext = ciphertext.encode("utf-8")
    try:
        return _get_fernet().decrypt(ciphertext).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Failed to decrypt API key") from exc
