from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from datetime import datetime
from .base import Base

class LiveSession(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True) # session_id
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    total_score = Column(Float, default=0.0)
    total_gifts = Column(Integer, default=0)
