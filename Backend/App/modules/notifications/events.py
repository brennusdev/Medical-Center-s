"""MED V7 — Event emitters: domínio → NotificationService.

Não espalha criação de notificações nas rotas: os services chamam estas funções.
Todas são best-effort — falha de notificação nunca quebra o fluxo de negócio.
Preparado para trocar `emit` por enfileiramento assíncrono (Queue/Worker) no futuro.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from App.modules.notifications.models import NotificationType
from App.modules.notifications.service import NotificationService

# Papéis do "contexto autorizado" que acompanham o atendimento (V9 trará RBAC).
AUTHORIZED_CONTEXT_ROLES = ("DOCTOR", "NURSE", "RECEPTIONIST", "HOSPITAL", "ADMIN")


def _notify(db: Session, user_id: int, type_: NotificationType, title: str,
            message: str = "", resource_type: str | None = None,
            resource_id: int | None = None) -> None:
    try:
        NotificationService(db).emit(
            user_id=user_id, type_=type_, title=title, message=message,
            related_resource_type=resource_type, related_resource_id=resource_id,
        )
    except Exception:  # noqa: BLE001 — best-effort por design
        db.rollback()


def notify_authorized_context(db: Session, type_: NotificationType, title: str,
                              message: str = "", resource_type: str | None = None,
                              resource_id: int | None = None) -> None:
    from App.modules.users.models import User
    stmt = select(User).where(User.role.in_(AUTHORIZED_CONTEXT_ROLES))
    for user in db.scalars(stmt).all():
        _notify(db, user.id, type_, title, message, resource_type, resource_id)


# -- Eventos de domínio --------------------------------------------------------


def on_care_request_created(db: Session, care_request) -> None:
    _notify(
        db, care_request.patient_id, NotificationType.CARE_REQUEST_RECEIVED,
        "Solicitação recebida",
        f"Sua solicitação de {care_request.specialty} foi recebida.",
        "care_request", care_request.id,
    )


def on_queue_position_changed(db: Session, queue, previous_position: int | None,
                              new_position: int) -> None:
    from App.modules.care_requests.models import CareRequest
    care = db.get(CareRequest, queue.care_request_id)
    if care is None:
        return
    _notify(
        db, care.patient_id, NotificationType.QUEUE_POSITION_CHANGED,
        "Sua posição na fila foi atualizada.",
        f"Nova posição: {new_position}.",
        "queue", queue.id,
    )


def on_queue_priority_changed(db: Session, queue) -> None:
    from App.modules.care_requests.models import CareRequest
    care = db.get(CareRequest, queue.care_request_id)
    if care is None:
        return
    _notify(
        db, care.patient_id, NotificationType.QUEUE_PRIORITY_CHANGED,
        "Sua solicitação foi atualizada.",
        f"Prioridade alterada para {queue.priority.value}.",
        "queue", queue.id,
    )


def on_patient_status_updated(db: Session, status_update) -> None:
    notify_authorized_context(
        db, NotificationType.PATIENT_STATUS_UPDATED,
        "Nova atualização do paciente disponível.",
        f"O paciente informou {status_update.state.value} (intensidade {status_update.severity}/10).",
        "patient_status_update", status_update.id,
    )


def on_medical_evaluation_created(db: Session, evaluation) -> None:
    from App.modules.care_requests.models import CareRequest
    care = db.get(CareRequest, evaluation.care_request_id)
    if care is None:
        return
    _notify(
        db, care.patient_id, NotificationType.MEDICAL_EVALUATION_CREATED,
        "Seu atendimento recebeu uma nova atualização.",
        "Uma avaliação profissional foi registrada.",
        "medical_evaluation", evaluation.id,
    )


def on_appointment_scheduled(db: Session, appointment) -> None:
    _notify(
        db, appointment.patient_id, NotificationType.APPOINTMENT_SCHEDULED,
        "Consulta agendada.",
        f"{appointment.specialty} em {appointment.scheduled_at:%d/%m/%Y %H:%M}.",
        "appointment", appointment.id,
    )
