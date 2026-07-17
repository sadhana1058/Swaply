"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import auth, google
from app.core.config import settings


def create_app() -> FastAPI:
    is_dev = settings.ENVIRONMENT != "prod"
    app = FastAPI(
        title="New CRUD Demo — Auth API",
        version="1.0.0",
        docs_url="/docs" if is_dev else None,
        redoc_url=None,
    )

    # Signed session cookie — required by Authlib to hold the OAuth `state`.
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
        same_site=settings.COOKIE_SAMESITE,
        https_only=settings.COOKIE_SECURE,
    )

    # CORS: credentialed requests require an explicit origin (never "*").
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(google.router)

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
