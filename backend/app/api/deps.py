"""Shared FastAPI dependencies: current-user resolution and CSRF enforcement."""

import uuid

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import csrf_tokens_match, decode_token
from app.crud import user as user_crud
from app.db.session import get_db
from app.models.user import User

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
)


async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    """Resolve the user from the access-token cookie."""
    token = request.cookies.get(settings.ACCESS_COOKIE)
    if not token:
        raise _CREDENTIALS_ERROR
    try:
        payload = decode_token(token, expected_type="access")
        subject = payload.get("sub")
        if not subject:
            raise _CREDENTIALS_ERROR
        user_id = uuid.UUID(subject)
    except (jwt.PyJWTError, ValueError):
        raise _CREDENTIALS_ERROR

    user = await user_crud.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise _CREDENTIALS_ERROR
    return user


async def enforce_csrf(request: Request) -> None:
    """Double-submit CSRF check for state-changing requests.

    The SPA reads the (non-HttpOnly) csrf cookie and echoes it in the header;
    an attacker's cross-site request can send the cookie but not read/set the header.
    """
    cookie = request.cookies.get(settings.CSRF_COOKIE)
    header = request.headers.get(settings.CSRF_HEADER)
    if not csrf_tokens_match(cookie, header):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing or invalid",
        )
