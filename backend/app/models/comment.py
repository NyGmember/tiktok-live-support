from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from datetime import datetime
from .base import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.tiktok_id"), index=True)
    session_id = Column(String, ForeignKey("sessions.id"), index=True)
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_used = Column(Boolean, default=False)  # For "Question" feature
