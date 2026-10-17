from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SavedItem(Base):
    """A job or event saved by one student through the assistant."""

    __tablename__ = "saved_items"
    __table_args__ = (UniqueConstraint("student_id", "item_type", "item_id", name="uq_student_item"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.account_id", ondelete="CASCADE"), nullable=False)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    item_id: Mapped[int] = mapped_column(nullable=False)
    saved_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
