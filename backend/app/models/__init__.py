"""Import models so `app.db.base.Base.metadata` is fully populated for Alembic."""

from app.models.refresh_token import RefreshToken
from app.models.user import User

__all__ = ["User", "RefreshToken"]
