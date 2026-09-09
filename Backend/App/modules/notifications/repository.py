"""MED V7 — Data access layer for notifications (no business rules here)."""

from sqlalchemy import func, select
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

    # -- MED V11 — paginação ---------------------------------------------------
    def list_by_user_paged(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> tuple[list[Notification], int]:
        """Lista paginada com total exato (page-based).

        DECISÃO DE PAGINAÇÃO (V11): page-based (limit/offset + COUNT total).
        - Notificações são navegadas por página na UI (sino/aba), com total
          exibido — keyset complicaria o contrato sem ganho real: o usuário
          raramente navega além de poucas páginas.
        - Ordenação por (created_at desc, id desc) usa o índice composto
          ix_notifications_user_created (user_id, created_at).
        - COUNT no banco (nunca len da lista carregada).
        """
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .limit(limit)
            .offset(offset)
        )
        items = list(self.db.scalars(stmt).all())
        total = self.db.scalar(
            select(func.count()).select_from(Notification).where(Notification.user_id == user_id)
        )
        return items, int(total or 0)

    def mark_read(self, notification: Notification) -> Notification:
        notification.read = True
        self.db.commit()
        self.db.refresh(notification)
        return notification
