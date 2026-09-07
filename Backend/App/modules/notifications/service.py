"""MED V7 — NotificationService: única camada que cria notificações.

Arquitetura (sem mensageria nesta versão):
    Evento de domínio → NotificationService.emit(...) → Repository → PostgreSQL

Preparado para processamento assíncrono futuro (Queue/Worker/Email/Push/SMS):
todos os emissores passam por `emit`, que é o ponto único de extensão.
"""

from sqlalchemy.orm import Session

from App.modules.notifications.models import Notification, NotificationType
from App.modules.notifications.repository import NotificationRepository


class NotFoundError(Exception):
    """Requested entity does not exist."""


class ValidationError(Exception):
    """Business rule violation."""


class AuthorizationError(Exception):
    """Actor not allowed to perform the operation."""


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.repo = NotificationRepository(db)

    # -- Emissão (ponto único de extensão para Queue/Worker futuro) -----------

    def emit(
        self,
        user_id: int,
        type_: NotificationType,
        title: str,
        message: str = "",
        related_resource_type: str | None = None,
        related_resource_id: int | None = None,
    ) -> Notification | None:
        """Cria uma notificação. Não lança erro se o usuário não existir:
        emissão é best-effort e nunca deve quebrar o fluxo de negócio."""
        if user_id <= 0:
            return None
        notification = Notification(
            user_id=user_id,
            type=type_,
            title=title[:200],
            message=(message or "")[:500],
            read=False,
            related_resource_type=related_resource_type,
            related_resource_id=related_resource_id,
        )
        return self.repo.create(notification)

    # -- Leitura (usuário só vê as próprias notificações) ----------------------

    def get_for_user(self, notification_id: int, user_id: int) -> Notification:
        notification = self.repo.get(notification_id)
        if notification is None:
            raise NotFoundError(f"Notificação {notification_id} não encontrada")
        if notification.user_id != user_id:
            raise AuthorizationError("Usuário só pode visualizar as próprias notificações")
        return notification

    def list_by_user(self, user_id: int) -> list[Notification]:
        if user_id <= 0:
            raise ValidationError("user_id deve ser um inteiro positivo")
        return self.repo.list_by_user(user_id)

    def mark_read(self, notification_id: int, user_id: int) -> Notification:
        notification = self.get_for_user(notification_id, user_id)
        return self.repo.mark_read(notification)
