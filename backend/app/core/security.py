"""
Security utilities: API-key hashing, Fernet encryption, bcrypt passwords, JWT.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ── bcrypt password context ───────────────────────────────────────────────────
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password with bcrypt."""
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against its bcrypt hash."""
    return _pwd_context.verify(plain, hashed)


# ── API key functions ─────────────────────────────────────────────────────────

def hash_api_key(key: str) -> str:
    """HMAC-SHA256 of the raw key using SECRET_KEY as HMAC key."""
    return hmac.new(
        settings.SECRET_KEY.encode(),
        key.encode(),
        hashlib.sha256,
    ).hexdigest()


def verify_api_key(raw: str, stored_hash: str) -> bool:
    """Constant-time comparison of HMAC digests."""
    expected = hash_api_key(raw)
    return hmac.compare_digest(expected, stored_hash)


def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new virtual API key.

    Returns:
        (raw_key, hashed_key, prefix)

    Format: "ig-" + 48 url-safe base64 chars (no padding).
    Only the first 8 chars of the random part are stored as prefix.
    """
    random_bytes = secrets.token_bytes(36)  # 36 bytes → 48 base64 chars
    random_part = base64.urlsafe_b64encode(random_bytes).decode().rstrip("=")
    raw_key = f"ig-{random_part}"
    hashed = hash_api_key(raw_key)
    prefix = random_part[:8]
    return raw_key, hashed, prefix


# ── Fernet credential encryption ─────────────────────────────────────────────

def _get_fernet() -> Fernet:
    key = settings.FERNET_KEY
    # Pad if needed (Fernet requires exact 44-char url-safe base64)
    padding = 4 - len(key) % 4
    if padding != 4:
        key = key + "=" * padding
    return Fernet(key.encode())


def encrypt_credential(plaintext: str) -> str:
    """Encrypt a provider credential string. Returns base64-encoded ciphertext."""
    fernet = _get_fernet()
    return fernet.encrypt(plaintext.encode()).decode()


def decrypt_credential(ciphertext: str) -> str:
    """Decrypt a Fernet-encrypted credential."""
    fernet = _get_fernet()
    return fernet.decrypt(ciphertext.encode()).decode()


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Raises:
        jose.JWTError: if the token is invalid or expired.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
