from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Event(Base):
    """A recruiting event hosted by one company."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.account_id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(190))
    description: Mapped[str | None] = mapped_column(Text)
    event_date: Mapped[date] = mapped_column(Date)
    event_time: Mapped[time | None] = mapped_column(Time)
    location: Mapped[str | None] = mapped_column(String(190))
    eligibility: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    company: Mapped["Company"] = relationship()
