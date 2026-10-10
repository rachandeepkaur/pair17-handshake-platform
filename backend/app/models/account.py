from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AccountRole(str, PyEnum):
    STUDENT = "student"
    COMPANY = "company"


class Account(Base):
    """Shared login record for students and companies."""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(190), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[AccountRole] = mapped_column(
        Enum(AccountRole, name="account_role"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    student: Mapped["Student | None"] = relationship(
        back_populates="account",
        uselist=False,
    )
