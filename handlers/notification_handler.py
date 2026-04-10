"""HTTP handlers for notification endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from conf.database import get_db_session
from services.notification_service import (
    create_notification,
    get_notifications,
    mark_all_as_read,
    mark_as_read,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["Notifications"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class NotificationCreateRequest(BaseModel):
    user_id: int
    title: str
    message: str
    category: str = "info"


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    category: str
    is_read: bool
    created_at: datetime


class MarkReadResponse(BaseModel):
    success: bool
    detail: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/", response_model=NotificationResponse, status_code=201)
async def create(
    req: NotificationCreateRequest,
    db: Session = Depends(get_db_session),
):
    """Create a new notification for a user."""
    notification = create_notification(
        db,
        user_id=req.user_id,
        title=req.title,
        message=req.message,
        category=req.category,
    )
    return NotificationResponse(
        id=notification.id,
        user_id=notification.user_id,
        title=notification.title,
        message=notification.message,
        category=notification.category,
        is_read=notification.is_read,
        created_at=notification.created_at,
    )


@router.get("/", response_model=list[NotificationResponse])
async def list_notifications(
    user_id: int = Query(..., description="ID of the user whose notifications to fetch"),
    unread_only: bool = Query(False, description="Return only unread notifications"),
    db: Session = Depends(get_db_session),
):
    """List notifications for a given user."""
    notifications = get_notifications(db, user_id=user_id, unread_only=unread_only)
    return [
        NotificationResponse(
            id=n.id,
            user_id=n.user_id,
            title=n.title,
            message=n.message,
            category=n.category,
            is_read=n.is_read,
            created_at=n.created_at,
        )
        for n in notifications
    ]


@router.patch("/{notification_id}/read", response_model=MarkReadResponse)
async def mark_notification_read(
    notification_id: int,
    user_id: int = Query(..., description="ID of the owning user"),
    db: Session = Depends(get_db_session),
):
    """Mark a single notification as read."""
    updated = mark_as_read(db, notification_id=notification_id, user_id=user_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Notification not found or already read")
    return MarkReadResponse(success=True, detail="Notification marked as read")


@router.patch("/read-all", response_model=MarkReadResponse)
async def mark_all_read(
    user_id: int = Query(..., description="ID of the owning user"),
    db: Session = Depends(get_db_session),
):
    """Mark all notifications for a user as read."""
    count = mark_all_as_read(db, user_id=user_id)
    return MarkReadResponse(success=True, detail=f"{count} notification(s) marked as read")