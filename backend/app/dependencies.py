from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.database import get_db
from app.models.account import Account

# auto_error=False so a missing token goes through our own 401 message
# instead of FastAPI's default 403.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Account:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Missing or malformed authorization header")

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise UnauthorizedError(str(exc)) from exc

    account = db.get(Account, int(payload["sub"]))
    if account is None:
        raise UnauthorizedError("Account no longer exists")
    return account


def require_student(account: Account = Depends(get_current_user)) -> Account:
    if account.role != "student":
        raise ForbiddenError("Student account required")
    return account


def require_company(account: Account = Depends(get_current_user)) -> Account:
    if account.role != "company":
        raise ForbiddenError("Company account required")
    return account
