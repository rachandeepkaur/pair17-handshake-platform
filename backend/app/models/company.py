from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), primary_key=True)
    company_name = Column(String(190), nullable=False, index=True)
    location = Column(String(190), nullable=False)
    description = Column(Text, nullable=True)
    contact_info = Column(String(255), nullable=True)
    profile_picture_path = Column(String(255), nullable=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    account = relationship("Account")
