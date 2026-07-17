"""Password hashing (argon2), JWT encode/decode, and CSRF token helpers."""

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

# argon2 is the current OWASP-recommended password hash.
_password_hash = PasswordHash.recommended()


# --- Passwords --------------------------------------------------------------

def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    return _password_hash.verify(password, hashed)


# --- JWTs -------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(subject: str) -> str:
    expire = _now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "type": "access",
        "iat": _now(),
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    """Return (encoded_jwt, jti, expires_at). The jti identifies this token in the DB."""
    jti = uuid.uuid4().hex
    expire = _now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": subject,
        "type": "refresh",
        "jti": jti,
        "iat": _now(),
        "exp": expire,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expire


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    """Decode & validate a JWT, raising jwt exceptions on failure/expiry/type-mismatch."""
    payload = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("unexpected token type")
    return payload


def hash_jti(jti: str) -> str:
    """SHA-256 of the refresh jti; this is what we persist (never the raw token)."""
    return hashlib.sha256(jti.encode()).hexdigest()


# --- CSRF (double-submit token) ---------------------------------------------

def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def csrf_tokens_match(cookie_value: str | None, header_value: str | None) -> bool:
    if not cookie_value or not header_value:
        return False
    return hmac.compare_digest(cookie_value, header_value)
