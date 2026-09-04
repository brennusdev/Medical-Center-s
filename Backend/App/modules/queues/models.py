"""MED V4 — SQLAlchemy models for queues and prioritization.

REGRAS DE SEGURANÇA (obrigatórias):
- A prioridade operacional NÃO representa diagnóstico médico.
- O sistema NÃO diagnostica o paciente e NÃO decide sozinho uma prioridade
  clínica definitiva. Prioridade é sempre atribuída por um usuário autorizado
  do domínio e cada mudança fica registrada em QueueEvent com o ator.
- O histórico (QueueEvent) é imutável pela lógica normal da aplicação.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from App.core.database import Base


class QueueStatus(str, enum.Enum):
    """Status operacionais de uma entrada na fila (MED V4)."""

    WAITING = "WAITING"
    IN_REVIEW = "IN_REVIEW"
    REFERRED = "REFERRED"
    SCHEDULED = "SCHEDULED"
    REMOVED = "REMOVED"
    COMPLETED = "COMPLETED"


class QueuePriority(str, enum.Enum):
    """Prioridade OPERACIONAL (não clínica, não diagnóstico) — atribuída por usuário autorizado."""

    NORMAL = "NORMAL"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class QueueEventType(str, enum.Enum):
    """Tipos de evento do histórico da fila."""

    CREATED = "CREATED"
    POSITION_CHANGED = "POSITION_CHANGED"
    PRIORITY_CHANGED = "PRIORITY_CHANGED"
    STATUS_CHANGED = "STATUS_CHANGED"
    REFERRED = "REFERRED"
    REMOVED = "REMOVED"


class Queue(Base):
    """Entrada de uma CareRequest na fila de uma especialidade (MED V4)."""

    __tablename__ = "queues"
    __table_args__ = (
        Index("ix_queues_specialty_status", "specialty", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    care_request_id: Mapped[int] = mapped_column(
        ForeignKey("care_requests.id"), index=True, nullable=False
    )
    specialty: Mapped[str] = mapped_column(String(100), nullable=False)
    hospital_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # opcional (sem FK: módulo não existe)
    status: Mapped[QueueStatus] = mapped_column(
        Enum(QueueStatus, name="queue_status"),
        default=QueueStatus.WAITING,
        nullable=False,
    )
    priority: Mapped[QueuePriority] = mapped_column(
        Enum(QueuePriority, name="queue_priority"),
        default=QueuePriority.NORMAL,
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    entered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    events: Mapped[list["QueueEvent"]] = relationship(
        back_populates="queue", cascade="all, delete-orphan", order_by="QueueEvent.created_at"
    )


class QueueEvent(Base):
    """Evento imutável do histórico de uma entrada na fila (MED V4)."""

    __tablename__ = "queue_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    queue_id: Mapped[int] = mapped_column(ForeignKey("queues.id"), index=True, nullable=False)
    event_type: Mapped[QueueEventType] = mapped_column(
        Enum(QueueEventType, name="queue_event_type"), nullable=False
    )
    previous_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    new_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    previous_priority: Mapped[QueuePriority | None] = mapped_column(
        Enum(QueuePriority, name="queue_priority"), nullable=True
    )
    new_priority: Mapped[QueuePriority | None] = mapped_column(
        Enum(QueuePriority, name="queue_priority"), nullable=True
    )
    description: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    actor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # usuário responsável (opcional)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    queue: Mapped[Queue] = relationship(back_populates="events")
