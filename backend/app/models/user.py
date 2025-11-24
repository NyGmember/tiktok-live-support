from sqlalchemy import Column, String, DateTime
from datetime import datetime
from .base import Base


class User(Base):
    __tablename__ = "users"

    tiktok_id = Column(String, primary_key=True, index=True)
    nickname = Column(String)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
