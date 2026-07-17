"""Database operations for users."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User


async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.get(User, user_id)


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession, *, email: str, password: str, full_name: str | None = None
) -> User:
    user = User(
        email=email.lower(),
        hashed_password=hash_password(password),
        full_name=full_name,
        is_verified=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def upsert_oauth_user(
    db: AsyncSession,
    *,
    email: str,
    full_name: str | None,
    provider: str,
    sub: str,
) -> User:
    """Find a user by email and link the OAuth identity, or create a new verified user."""
    user = await get_by_email(db, email)
    if user is None:
        user = User(
            email=email.lower(),
            full_name=full_name,
            hashed_password=None,
            is_verified=True,  # email is provider-verified
            oauth_provider=provider,
            oauth_sub=sub,
        )
        db.add(user)
    else:
        # Link the OAuth identity to the existing account.
        user.oauth_provider = provider
        user.oauth_sub = sub
        user.is_verified = True
        if full_name and not user.full_name:
            user.full_name = full_name
    await db.commit()
    await db.refresh(user)
    return user
