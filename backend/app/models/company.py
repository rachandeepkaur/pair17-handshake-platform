from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Company(Base):
    """Employer profile linked one-to-one with an account."""

    __tablename__ = "companies"

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    company_name: Mapped[str] = mapped_column(String(190), index=True)
    location: Mapped[str] = mapped_column(String(190))
    description: Mapped[str | None] = mapped_column(Text)
    contact_info: Mapped[str | None] = mapped_column(String(255))
    profile_picture_path: Mapped[str | None] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    account: Mapped["Account"] = relationship()
