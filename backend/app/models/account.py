from sqlalchemy import TIMESTAMP, Column, Enum, Integer, String, func

from app.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(190), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("student", "company", name="account_role"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
