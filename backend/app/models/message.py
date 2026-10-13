from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Conversation(Base):
    """The single message thread between one company and one student."""

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.account_id", ondelete="CASCADE"))
    student_id: Mapped[int] = mapped_column(ForeignKey("students.account_id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime)

    company: Mapped["Company"] = relationship()
    student: Mapped["Student"] = relationship()


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"))
    sender_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"))
    body: Mapped[str] = mapped_column(Text)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id", ondelete="SET NULL"))
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    read_at: Mapped[datetime | None] = mapped_column(DateTime)

    job: Mapped["Job | None"] = relationship()
    event: Mapped["Event | None"] = relationship()
