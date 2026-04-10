"""Service layer for notification management."""

import logging
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from models.notification import Notification

logger = logging.getLogger(__name__)


def create_notification(
    db: Session, user_id: int, title: str, message: str, category: str = "info"
) -> Notification:
    """Create and persist a new notification for the given user."""
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        category=category,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    logger.info("Created notification id=%d for user=%d", notification.id, user_id)
    return notification


def get_notifications(
    db: Session, user_id: int, unread_only: bool = False
) -> list[Notification]:
    """Return notifications for a user, optionally filtering to unread only."""
    stmt = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.is_read == False)  # noqa: E712
    stmt = stmt.order_by(Notification.created_at.desc())
    return list(db.execute(stmt).scalars().all())


def mark_as_read(db: Session, notification_id: int, user_id: int) -> bool:
    """Mark a single notification as read. Returns True if updated."""
    stmt = (
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user_id)
        .values(is_read=True)
    )
    result = db.execute(stmt)
    db.commit()
    updated = result.rowcount > 0
    if updated:
        logger.info("Marked notification id=%d as read for user=%d", notification_id, user_id)
    return updated


def mark_all_as_read(db: Session, user_id: int) -> int:
    """Mark all notifications for a user as read. Returns count of updated rows."""
    stmt = (
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        .values(is_read=True)
    )
    result = db.execute(stmt)
    db.commit()
    logger.info("Marked %d notifications as read for user=%d", result.rowcount, user_id)
    return result.rowcount
