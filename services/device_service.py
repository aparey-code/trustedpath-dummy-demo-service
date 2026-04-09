"""Device management and endpoint posture evaluation."""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.device import Device
from conf.settings import FEATURE_FLAG_POSTURE_CHECK

logger = logging.getLogger(__name__)

TRUST_LEVEL_THRESHOLDS = {
    "trusted": 80.0,
    "moderate": 50.0,
    "untrusted": 0.0,
}


def register_device(
    db: Session,
    owner_id: int,
    device_key: str,
    platform: str,
    os_version: str | None = None,
    hostname: str | None = None,
) -> Device:
    """Register a new device for a user."""
    device = Device(
        device_key=device_key,
        owner_id=owner_id,
        platform=platform,
        os_version=os_version,
        hostname=hostname,
        trust_level="unknown",
    )
    db.add(device)
    db.flush()
    logger.info("Registered device %s for user %d", device_key[:12], owner_id)
    return device


def update_posture(db: Session, device_key: str, posture_score: float) -> Device | None:
    """Update a device's posture score and recalculate trust level."""
    stmt = select(Device).where(Device.device_key == device_key)
    device = db.execute(stmt).scalar_one_or_none()

    if device is None:
        logger.warning("Posture update for unknown device: %s", device_key[:12])
        return None

    device.posture_score = posture_score
    device.last_seen_at = datetime.now(timezone.utc)

    if FEATURE_FLAG_POSTURE_CHECK:
        device.trust_level = _compute_trust_level(posture_score)

    return device


def get_user_devices(db: Session, owner_id: int) -> list[Device]:
    """Get all devices belonging to a user."""
    stmt = select(Device).where(Device.owner_id == owner_id)
    return list(db.execute(stmt).scalars().all())


def _compute_trust_level(score: float) -> str:
    """Map a numeric posture score to a trust level string."""
    for level, threshold in TRUST_LEVEL_THRESHOLDS.items():
        if score >= threshold:
            return level
    return "untrusted"
