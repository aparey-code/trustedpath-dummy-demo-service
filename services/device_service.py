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
    is_managed: bool = False,
) -> Device:
    """Register a new device for a user."""
    existing = db.execute(select(Device).where(Device.device_key == device_key)).scalar_one_or_none()
    if existing is not None:
        raise ValueError("Device already registered")

    device = Device(
        device_key=device_key,
        owner_id=owner_id,
        platform=platform,
        os_version=os_version,
        hostname=hostname,
        is_managed=is_managed,
        trust_level="managed" if is_managed else "unknown",
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


def get_device(db: Session, owner_id: int, device_key: str) -> Device | None:
    """Get a specific device belonging to a user."""
    stmt = select(Device).where(Device.owner_id == owner_id, Device.device_key == device_key)
    return db.execute(stmt).scalar_one_or_none()


def update_device(
    db: Session,
    owner_id: int,
    device_key: str,
    *,
    os_version: str | None = None,
    hostname: str | None = None,
    is_managed: bool | None = None,
    posture_score: float | None = None,
) -> Device | None:
    """Update editable fields for a user-owned device."""
    device = get_device(db, owner_id, device_key)
    if device is None:
        return None

    if os_version is not None:
        device.os_version = os_version
    if hostname is not None:
        device.hostname = hostname
    if is_managed is not None:
        device.is_managed = is_managed
    if posture_score is not None:
        device.posture_score = posture_score
        device.last_seen_at = datetime.now(timezone.utc)

    if FEATURE_FLAG_POSTURE_CHECK and device.posture_score is not None:
        device.trust_level = _compute_trust_level(device.posture_score)
    elif device.is_managed:
        device.trust_level = "managed"
    elif is_managed is not None:
        device.trust_level = "unknown"

    db.flush()
    return device


def delete_device(db: Session, owner_id: int, device_key: str) -> bool:
    """Delete a specific device belonging to a user."""
    device = get_device(db, owner_id, device_key)
    if device is None:
        return False

    db.delete(device)
    db.flush()
    return True


def _compute_trust_level(score: float) -> str:
    """Map a numeric posture score to a trust level string."""
    for level, threshold in TRUST_LEVEL_THRESHOLDS.items():
        if score >= threshold:
            return level
    return "untrusted"


class DeviceService:
    """DB-backed service wrapper used by the device handler."""

    def __init__(self, db: Session):
        self.db = db

    def register_device(self, *, owner_id: int, payload) -> Device:
        platform = payload.platform.value if hasattr(payload.platform, "value") else payload.platform
        return register_device(
            self.db,
            owner_id=owner_id,
            device_key=payload.device_key,
            platform=platform,
            os_version=payload.os_version,
            hostname=payload.hostname,
            is_managed=payload.is_managed,
        )

    def list_devices(self, *, owner_id: int) -> list[Device]:
        return get_user_devices(self.db, owner_id)

    def get_device(self, *, owner_id: int, device_key: str) -> Device | None:
        return get_device(self.db, owner_id, device_key)

    def update_device(self, *, owner_id: int, device_key: str, changes: dict) -> Device | None:
        return update_device(self.db, owner_id, device_key, **changes)

    def delete_device(self, *, owner_id: int, device_key: str) -> bool:
        return delete_device(self.db, owner_id, device_key)
