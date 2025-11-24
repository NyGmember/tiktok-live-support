from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime
from .base import Base


class Gift(Base):
    __tablename__ = "gifts"

    gift_id = Column(String, primary_key=True, index=True)
    name = Column(String)
    image_url = Column(String, nullable=True)
    diamond_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
