"""MED V7 — Notification model.

Regras: histórico preservado (nunca apagado); marcar como lida apenas altera
`read`; toda notificação tem timestamp; campos opcionais de recurso relacionado
direcionam o usuário ao atendimento correspondente.
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from App.core.database import Base


class NotificationType(str, enum.Enum):
    CARE_REQUEST_CREATED = "CARE_REQUEST_CREATED"
    CARE_REQUEST_RECEIVED = "CARE_REQUEST_RECEIVED"
    QUEUE_POSITION_CHANGED = "QUEUE_POSITION_CHANGED"
    QUEUE_PRIORITY_CHANGED = "QUEUE_PRIORITY_CHANGED"
    CARE_REQUEST_REFERRED = "CARE_REQUEST_REFERRED"
    APPOINTMENT_AVAILABLE = "APPOINTMENT_AVAILABLE"
    APPOINTMENT_SCHEDULED = "APPOINTMENT_SCHEDULED"
    APPOINTMENT_CANCELLED = "APPOINTMENT_CANCELLED"
    APPOINTMENT_RESCHEDULED = "APPOINTMENT_RESCHEDULED"
    PATIENT_STATUS_UPDATED = "PATIENT_STATUS_UPDATED"
    MEDICAL_EVALUATION_CREATED = "MEDICAL_EVALUATION_CREATED"
    DOCUMENT_RECEIVED = "DOCUMENT_RECEIVED"


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Direcionamento opcional ao recurso correspondente (ex.: care_request).
    related_resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    related_resource_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User", viewonly=True)
