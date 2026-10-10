from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.database import SessionLocal
from app.models.account import Account


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Account:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("Missing or malformed authorization header")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise UnauthorizedError(str(exc)) from exc

    account = db.get(Account, int(payload["sub"]))
    if account is None:
        raise UnauthorizedError("Account no longer exists")
    return account


def require_student(account: Account = Depends(get_current_user)) -> Account:
    if account.role != "student":
        raise UnauthorizedError("Student account required")
    return account


def require_company(account: Account = Depends(get_current_user)) -> Account:
    if account.role != "company":
        raise UnauthorizedError("Company account required")
    return account
