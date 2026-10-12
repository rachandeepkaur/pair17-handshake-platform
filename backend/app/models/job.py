from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

JOB_CATEGORIES = ("full_time", "part_time", "on_campus", "internship")


class Job(Base):
    """A job posting owned by one company."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.account_id", ondelete="CASCADE"),
    )
    title: Mapped[str] = mapped_column(String(190))
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(Enum(*JOB_CATEGORIES, name="job_category"))
    city: Mapped[str] = mapped_column(String(100))
    location: Mapped[str | None] = mapped_column(String(190))
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False)
    salary: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    skills_required: Mapped[str | None] = mapped_column(Text)
    posting_date: Mapped[date] = mapped_column(Date)
    deadline: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    company: Mapped["Company"] = relationship()
