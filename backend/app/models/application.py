from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

APPLICATION_STATUSES = ("Pending", "Reviewed", "Declined")


class Application(Base):
    """A student's application to one job, with the uploaded resume."""

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.account_id", ondelete="CASCADE"))
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"))
    resume_path: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        Enum(*APPLICATION_STATUSES, name="application_status"),
        default="Pending",
    )
    applied_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    student: Mapped["Student"] = relationship()
    job: Mapped["Job"] = relationship()
