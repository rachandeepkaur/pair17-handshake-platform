from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.permissions import ROLE_LABELS, has_permission
from app.core.security import decode_access_token
from app.database import get_db
from app.models.account import Account
from app.models.company_member import CompanyMember

# auto_error=False so a missing token goes through our own 401 message
# instead of FastAPI's default 403.
bearer_scheme = HTTPBearer(auto_error=False)

_ACTIVITY_WRITE_INTERVAL = timedelta(minutes=5)


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


@dataclass
class CompanyContext:
    """Who is calling and which company they act for. `company_id` is the
    company's id (its owner account id), not necessarily `account.id`."""

    account: Account
    member: CompanyMember

    @property
    def company_id(self) -> int:
        return self.member.company_id

    @property
    def role(self) -> str:
        return self.member.role

    def can(self, permission: str) -> bool:
        return has_permission(self.member.role, permission)


def require_company(
    account: Account = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CompanyContext:
    if account.role != "company":
        raise ForbiddenError("Company account required")

    member = db.scalar(select(CompanyMember).where(CompanyMember.account_id == account.id))
    if member is None:
        raise ForbiddenError("This account is not a member of any company")

    now = datetime.now()
    if member.last_active_at is None or now - member.last_active_at > _ACTIVITY_WRITE_INTERVAL:
        member.last_active_at = now
        db.commit()

    return CompanyContext(account=account, member=member)


def require_permission(permission: str):
    def dependency(ctx: CompanyContext = Depends(require_company)) -> CompanyContext:
        if not ctx.can(permission):
            raise ForbiddenError(f"Your role ({ROLE_LABELS[ctx.role]}) can't do this")
        return ctx

    return dependency
