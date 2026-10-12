from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Registration(Base):
    """A student's registration for one event."""

    __tablename__ = "registrations"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.account_id", ondelete="CASCADE"))
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    registered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    student: Mapped["Student"] = relationship()
    event: Mapped["Event"] = relationship()
