"""Issuing and rotating login sessions (tokens + cookies).

Kept separate from the route handlers so both the password and Google flows reuse it.
"""

import uuid

from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cookies import set_auth_cookies
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_csrf_token,
)
from app.crud import refresh_token as rt_crud
from app.models.user import User


async def issue_session(db: AsyncSession, response: Response, user: User) -> None:
    """Create access + refresh tokens for `user`, persist the refresh, set cookies."""
    subject = str(user.id)
    access = create_access_token(subject)
    refresh, jti, expires_at = create_refresh_token(subject)
    await rt_crud.store(db, user_id=user.id, jti=jti, expires_at=expires_at)
    csrf = generate_csrf_token()
    set_auth_cookies(response, access, refresh, csrf)


async def rotate_session(
    db: AsyncSession, response: Response, user_id: uuid.UUID
) -> None:
    """Issue a fresh access + refresh pair (used after revoking the presented one)."""
    subject = str(user_id)
    access = create_access_token(subject)
    refresh, jti, expires_at = create_refresh_token(subject)
    await rt_crud.store(db, user_id=user_id, jti=jti, expires_at=expires_at)
    csrf = generate_csrf_token()
    set_auth_cookies(response, access, refresh, csrf)
