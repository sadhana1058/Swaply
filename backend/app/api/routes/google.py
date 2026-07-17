"""Google OAuth 2.0 (OpenID Connect) sign-in routes."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud import user as user_crud
from app.db.session import get_db
from app.services.auth_session import issue_session
from app.services.google_oauth import get_oauth

router = APIRouter(prefix="/auth/google", tags=["auth:google"])


def _require_google_enabled() -> None:
    if not settings.google_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured on this server",
        )


@router.get("/login")
async def google_login(request: Request):
    """Kick off the OAuth dance: redirect the browser to Google's consent screen."""
    _require_google_enabled()
    oauth = get_oauth()
    return await oauth.google.authorize_redirect(request, settings.google_redirect_uri)


@router.get("/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """Google redirects here with a code; exchange it, upsert the user, set cookies."""
    _require_google_enabled()
    oauth = get_oauth()
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google authentication failed",
        )

    userinfo = token.get("userinfo")
    if not userinfo or not userinfo.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google did not return an email",
        )
    return await complete_google_login(db, dict(userinfo))


async def complete_google_login(db: AsyncSession, userinfo: dict) -> RedirectResponse:
    """Upsert the Google user, issue a session, and redirect to the SPA home page.

    Extracted so tests can exercise the user-linking + cookie logic without Google.
    """
    user = await user_crud.upsert_oauth_user(
        db,
        email=userinfo["email"],
        full_name=userinfo.get("name"),
        provider="google",
        sub=str(userinfo.get("sub", "")),
    )
    redirect = RedirectResponse(
        url=f"{settings.FRONTEND_URL}/home",
        status_code=status.HTTP_302_FOUND,
    )
    await issue_session(db, redirect, user)
    return redirect
