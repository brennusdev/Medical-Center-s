"""MED V4 — API schemas (contract) for queues."""

import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class QueueCreate(BaseModel):
    """Payload para criar uma entrada na fila.

    `actor_id` identifica quem criou a entrada (opcional nesta versão, pois
    não há autenticação JWT ainda). Prioridade inicial é sempre NORMAL —
    o sistema NÃO atribui prioridade clínica automaticamente.
    """

    care_request_id: int = Field(gt=0, description="ID da solicitação de atendimento (CareRequest)")
    specialty: str = Field(min_length=2, max_length=100, description="Especialidade da fila")
    hospital_id: Optional[int] = Field(default=None, gt=0, description="Hospital (opcional)")
    actor_id: Optional[int] = Field(default=None, gt=0, description="Usuário responsável pela criação (opcional)")


class QueueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    care_request_id: int
    specialty: str
    hospital_id: Optional[int] = None
    status: enum.Enum  # QueueStatus
    priority: enum.Enum  # QueuePriority
    position: int
    entered_at: datetime
    updated_at: datetime


class QueuePriorityUpdate(BaseModel):
    """Payload para alterar a prioridade (apenas usuários autorizados no domínio).

    O paciente NÃO pode alterar a própria prioridade (403).
    """

    priority: QueuePriorityLiteral
    actor_id: int = Field(gt=0, description="Usuário responsável pela alteração")


class QueueEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    queue_id: int
    event_type: enum.Enum  # QueueEventType
    previous_position: Optional[int] = None
    new_position: Optional[int] = None
    previous_priority: Optional[enum.Enum] = None  # QueuePriority
    new_priority: Optional[enum.Enum] = None  # QueuePriority
    description: str
    actor_id: Optional[int] = None
    created_at: datetime


try:  # pragma: no cover - reexport do enum do models
    from App.modules.queues.models import QueuePriority as QueuePriorityLiteral
except ImportError:  # pragma: no cover
    QueuePriorityLiteral = enum.Enum  # type: ignore[assignment,misc]
