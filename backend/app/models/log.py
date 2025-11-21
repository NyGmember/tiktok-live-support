from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from .base import Base

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String) # INFO, WARNING, ERROR
    message = Column(Text)
    details = Column(Text, nullable=True) # JSON string or stack trace
