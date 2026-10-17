from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Preference(Base):
    """Optional saved job and event preferences for one student."""

    __tablename__ = "preferences"

    student_id: Mapped[int] = mapped_column(ForeignKey("students.account_id", ondelete="CASCADE"), primary_key=True)
    preferred_categories: Mapped[str | None] = mapped_column(String(255))
    preferred_cities: Mapped[str | None] = mapped_column(String(255))
    min_salary: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    preferred_skills: Mapped[str | None] = mapped_column(Text)
    remote_ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
