"""Database operations for refresh tokens (rotation + reuse detection)."""

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_jti
from app.models.refresh_token import RefreshToken


async def store(
    db: AsyncSession, *, user_id: uuid.UUID, jti: str, expires_at: datetime
) -> RefreshToken:
    token = RefreshToken(
        user_id=user_id,
        token_hash=hash_jti(jti),
        expires_at=expires_at,
        revoked=False,
    )
    db.add(token)
    await db.commit()
    return token


async def get_by_jti(db: AsyncSession, jti: str) -> RefreshToken | None:
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_jti(jti))
    )
    return result.scalar_one_or_none()


async def revoke(db: AsyncSession, token: RefreshToken) -> None:
    token.revoked = True
    await db.commit()


async def revoke_all_for_user(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Used on refresh-token reuse: nuke every active session for the user."""
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
        .values(revoked=True)
    )
    await db.commit()
