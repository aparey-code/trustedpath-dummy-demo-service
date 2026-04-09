"""Device model for Duo Desktop / endpoint health tracking."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from models.user import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_key = Column(String(255), unique=True, nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    platform = Column(String(50), nullable=False)
    os_version = Column(String(100))
    hostname = Column(String(255))
    is_managed = Column(Boolean, default=False)
    trust_level = Column(String(20), default="unknown")
    last_seen_at = Column(DateTime, nullable=True)
    posture_score = Column(Float, nullable=True)
    registered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="devices")

    @property
    def is_trusted(self) -> bool:
        return self.trust_level in ("trusted", "managed")
