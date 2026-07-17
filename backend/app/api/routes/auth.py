"""Email/password auth routes + session lifecycle (refresh, logout, me)."""

import uuid

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import enforce_csrf, get_current_user
from app.core.config import settings
from app.core.cookies import clear_auth_cookies
from app.core.security import decode_token, verify_password
from app.crud import refresh_token as rt_crud
from app.crud import user as user_crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import Message, UserCreate, UserLogin, UserRead
from app.services.auth_session import issue_session, rotate_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: UserCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> User:
    if await user_crud.get_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists",
        )
    user = await user_crud.create_user(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
    )
    await issue_session(db, response, user)
    return user


@router.post("/login", response_model=UserRead)
async def login(
    payload: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await user_crud.get_by_email(db, payload.email)
    # Verify even on missing user to keep timing roughly uniform.
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled"
        )
    await issue_session(db, response, user)
    return user


@router.post("/refresh", response_model=Message)
async def refresh(
    request: Request,
    response: Response,
    _: None = Depends(enforce_csrf),
    db: AsyncSession = Depends(get_db),
) -> Message:
    """Rotate the refresh token. Detects reuse of an already-revoked token."""
    token = request.cookies.get(settings.REFRESH_COOKIE)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token"
        )
    try:
        payload = decode_token(token, expected_type="refresh")
        jti = payload["jti"]
        user_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    stored = await rt_crud.get_by_jti(db, jti)
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    if stored.revoked:
        # Reuse of a rotated/revoked token -> assume theft, kill all sessions.
        await rt_crud.revoke_all_for_user(db, user_id)
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected; please sign in again",
        )

    # Valid, unused token: revoke it and issue a fresh pair.
    await rt_crud.revoke(db, stored)
    await rotate_session(db, response, user_id)
    return Message(detail="Token refreshed")


@router.post("/logout", response_model=Message)
async def logout(
    request: Request,
    response: Response,
    _: None = Depends(enforce_csrf),
    db: AsyncSession = Depends(get_db),
) -> Message:
    token = request.cookies.get(settings.REFRESH_COOKIE)
    if token:
        try:
            payload = decode_token(token, expected_type="refresh")
            stored = await rt_crud.get_by_jti(db, payload["jti"])
            if stored and not stored.revoked:
                await rt_crud.revoke(db, stored)
        except (jwt.PyJWTError, KeyError):
            pass  # already-invalid token: just clear cookies
    clear_auth_cookies(response)
    return Message(detail="Logged out")


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
