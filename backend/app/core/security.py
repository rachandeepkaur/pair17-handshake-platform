from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return a bcrypt hash; never store the plain-text password."""

    return password_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Compare a submitted password with its stored bcrypt hash."""

    return password_context.verify(plain_password, password_hash)


def create_access_token(
    subject: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT containing the account ID and role."""

    expires_at = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode a JWT or raise a consistent invalid-token error."""

    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise ValueError("Invalid or expired access token") from exc
