from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Student(Base):
    """Profile information linked one-to-one with an account."""

    __tablename__ = "students"

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(150))
    college_name: Mapped[str] = mapped_column(String(190))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    career_objective: Mapped[str | None] = mapped_column(Text)
    degree: Mapped[str | None] = mapped_column(String(100))
    major: Mapped[str | None] = mapped_column(String(100))
    graduation_year: Mapped[int | None] = mapped_column()
    cgpa: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    experience: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(30))
    skills: Mapped[str | None] = mapped_column(Text)
    profile_picture_path: Mapped[str | None] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    account: Mapped["Account"] = relationship(back_populates="student")
