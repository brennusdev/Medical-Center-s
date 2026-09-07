"""MED V7 — Data access layer for notifications (no business rules here)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from App.modules.notifications.models import Notification


class NotificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get(self, notification_id: int) -> Notification | None:
        return self.db.get(Notification, notification_id)

    def list_by_user(self, user_id: int) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
        )
        return list(self.db.scalars(stmt).all())

    def mark_read(self, notification: Notification) -> Notification:
        notification.read = True
        self.db.commit()
        self.db.refresh(notification)
        return notification
