from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

MEMBER_ROLES = ("owner", "admin", "recruiter", "hiring_manager", "viewer")
INVITABLE_ROLES = ("admin", "recruiter", "hiring_manager", "viewer")


class CompanyMember(Base):
    """An account that can act on behalf of a company, with a team role."""

    __tablename__ = "company_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.account_id", ondelete="CASCADE"))
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), unique=True)
    name: Mapped[str] = mapped_column(String(150))
    role: Mapped[str] = mapped_column(Enum(*MEMBER_ROLES, name="member_role"))
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    account: Mapped["Account"] = relationship()
    company: Mapped["Company"] = relationship()


class TeamInvitation(Base):
    """A pending invite. Only the SHA-256 of the invite token is stored."""

    __tablename__ = "team_invitations"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.account_id", ondelete="CASCADE"))
    email: Mapped[str] = mapped_column(String(190))
    name: Mapped[str] = mapped_column(String(150))
    role: Mapped[str] = mapped_column(Enum(*INVITABLE_ROLES, name="invitation_role"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    invited_by: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    company: Mapped["Company"] = relationship()
