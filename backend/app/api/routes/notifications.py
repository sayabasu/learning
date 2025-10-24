from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ...db import get_session
from ...models import Notification, User
from ...schemas import Message, NotificationRead, NotificationUpdate
from ..deps import get_current_active_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=List[NotificationRead])
def list_notifications(
    session: Session = Depends(get_session), current_user: User = Depends(get_current_active_user)
) -> List[Notification]:
    statement = select(Notification).where(Notification.user_id == current_user.id).order_by(Notification.created_at.desc())
    return session.exec(statement).all()


@router.patch("/{notification_id}", response_model=Message)
def update_notification(
    notification_id: int,
    update: NotificationUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> Message:
    notification = session.get(Notification, notification_id)
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = update.is_read
    session.add(notification)
    session.commit()
    return Message(message="Notification updated")
