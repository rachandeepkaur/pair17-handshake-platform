from dataclasses import dataclass
from datetime import timedelta

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo.database import Database

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.permissions import ROLE_LABELS, has_permission
from app.core.security import decode_access_token
from app.core.sessions import validate_session
from app.mongo import Doc, doc, get_db, utcnow

__all__ = ["get_db", "get_current_user", "require_student", "require_company", "require_permission", "CompanyContext"]

# auto_error=False so a missing token goes through our own 401 message
# instead of FastAPI's default 403.
bearer_scheme = HTTPBearer(auto_error=False)

_ACTIVITY_WRITE_INTERVAL = timedelta(minutes=5)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Database = Depends(get_db),
) -> Doc:
    """The account behind a valid token AND a live server-side session.

    The returned account carries `session` (the session document), so logout
    and password changes can revoke exactly this session.
    """

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Missing or malformed authorization header")

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise UnauthorizedError(str(exc)) from exc

    session = validate_session(db, payload)
    if session is None:
        raise UnauthorizedError("Session expired or signed out. Please sign in again.")

    account = doc(db.accounts.find_one({"_id": int(payload["sub"])}))
    if account is None:
        raise UnauthorizedError("Account no longer exists")
    account["session"] = session
    return account


def require_student(account: Doc = Depends(get_current_user)) -> Doc:
    if account.role != "student":
        raise ForbiddenError("Student account required")
    return account


@dataclass
class CompanyContext:
    """Who is calling and which company they act for. `company_id` is the
    company's id (its owner account id), not necessarily `account.id`."""

    account: Doc
    member: Doc

    @property
    def company_id(self) -> int:
        return self.member.company_id

    @property
    def role(self) -> str:
        return self.member.role

    def can(self, permission: str) -> bool:
        return has_permission(self.member.role, permission)


def require_company(
    account: Doc = Depends(get_current_user),
    db: Database = Depends(get_db),
) -> CompanyContext:
    if account.role != "company":
        raise ForbiddenError("Company account required")

    member = doc(db.company_members.find_one({"account_id": account.id}))
    if member is None:
        raise ForbiddenError("This account is not a member of any company")

    now = utcnow()
    if member.last_active_at is None or now - member.last_active_at > _ACTIVITY_WRITE_INTERVAL:
        db.company_members.update_one({"_id": member.id}, {"$set": {"last_active_at": now}})
        member["last_active_at"] = now

    return CompanyContext(account=account, member=member)


def require_permission(permission: str):
    def dependency(ctx: CompanyContext = Depends(require_company)) -> CompanyContext:
        if not ctx.can(permission):
            raise ForbiddenError(f"Your role ({ROLE_LABELS[ctx.role]}) can't do this")
        return ctx

    return dependency
