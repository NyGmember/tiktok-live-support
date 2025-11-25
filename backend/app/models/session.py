from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Enum
from datetime import datetime
from .base import Base
import enum


class SessionStatus(str, enum.Enum):
    STREAMING = "STREAMING"
    CLOSED = "CLOSED"


class LiveSession(Base):
    __tablename__ = "sessions"

    id = Column(String(32), primary_key=True, index=True)  # 32-char hash
    channel_name = Column(String, nullable=True)
    status = Column(Enum(SessionStatus), default=SessionStatus.STREAMING)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    is_active = Column(
        Boolean, default=True
    )  # Deprecated in favor of status, but kept for compatibility
    total_score = Column(Float, default=0.0)
    total_gifts = Column(Integer, default=0)
