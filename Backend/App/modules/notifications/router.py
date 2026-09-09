"""MED V7 — Notifications router. Thin: HTTP only, logic lives in service."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from App.core.database import get_db
from App.modules.auth.dependencies import check_ownership, get_current_user
from App.modules.notifications.schemas import NotificationRead
from App.modules.notifications.service import (
    AuthorizationError,
    NotFoundError,
    NotificationService,
    ValidationError,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_service(db: Session = Depends(get_db)) -> NotificationService:
    return NotificationService(db)


@router.get(
    "/user/{user_id}",
    response_model=list[NotificationRead],
    summary="Listar notificações do usuário (mais recente primeiro)",
)
def list_user_notifications(
    user_id: int,
    current=Depends(get_current_user),
    service: NotificationService = Depends(get_service),
):
    # V9 ownership: usuário autenticado só lista as próprias notificações.
    check_ownership(current, user_id)
    try:
        return service.list_by_user(user_id)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get(
    "/{notification_id}",
    response_model=NotificationRead,
    summary="Detalhar uma notificação",
)
def get_notification(notification_id: int, user_id: int, service: NotificationService = Depends(get_service)):
    """`user_id` é obrigatório como query param: usuário só vê as próprias notificações."""
    try:
        return service.get_for_user(notification_id, user_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationRead,
    summary="Marcar como lida (a notificação é preservada)",
)
def mark_read(
    notification_id: int,
    user_id: int,
    current=Depends(get_current_user),
    service: NotificationService = Depends(get_service),
):
    # V9 ownership: também aplicado na escrita (marcar como lida).
    check_ownership(current, user_id)
    try:
        return service.mark_read(notification_id, user_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
