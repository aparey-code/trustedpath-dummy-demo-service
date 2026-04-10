"""Access policy evaluation based on device trust and session state."""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.device import Device
from models.session import AuthSession

logger = logging.getLogger(__name__)

MINIMUM_TRUST_LEVELS = {
    "strict": ("trusted", "managed"),
    "standard": ("trusted", "managed", "moderate"),
    "permissive": ("trusted", "managed", "moderate", "unknown"),
}


def evaluate_access(
    db: Session, session_token: str, device_key: str, policy: str = "standard"
) -> dict:
    """Evaluate whether a session+device pair satisfies the given access policy.

    Returns a dict with 'allowed' (bool) and 'reason' (str).
    """
    allowed_levels = MINIMUM_TRUST_LEVELS.get(policy)
    if allowed_levels is None:
        logger.warning("Unknown policy requested: %s", policy)
        return {"allowed": False, "reason": f"Unknown policy: {policy}"}

    stmt = select(AuthSession).where(AuthSession.session_token == session_token)
    session = db.execute(stmt).scalar_one_or_none()

    if session is None or not session.is_valid:
        logger.info("Access denied: invalid or expired session")
        return {"allowed": False, "reason": "Invalid or expired session"}

    stmt = select(Device).where(Device.device_key == device_key)
    device = db.execute(stmt).scalar_one_or_none()

    if device is None:
        logger.info("Access denied: unknown device %s", device_key[:12])
        return {"allowed": False, "reason": "Unregistered device"}

    if device.owner_id != session.user_id:
        logger.warning(
            "Access denied: device %s not owned by session user %d",
            device_key[:12],
            session.user_id,
        )
        return {"allowed": False, "reason": "Device not owned by authenticated user"}

    if device.trust_level not in allowed_levels:
        logger.info(
            "Access denied: device trust_level=%s does not meet policy=%s",
            device.trust_level,
            policy,
        )
        return {
            "allowed": False,
            "reason": f"Device trust level '{device.trust_level}' does not meet '{policy}' policy",
        }

    logger.info(
        "Access granted: user=%d device=%s policy=%s",
        session.user_id,
        device_key[:12],
        policy,
    )
    return {"allowed": True, "reason": "Access granted"}


def list_policies() -> list[dict]:
    """Return available access policies and their accepted trust levels."""
    return [
        {"name": name, "accepted_trust_levels": list(levels)}
        for name, levels in MINIMUM_TRUST_LEVELS.items()
    ]
