"""MED V3 — SQLAlchemy model for care requests ("Preciso de atendimento").

Todos os campos clínicos (sintomas, desconforto, descrição) são RELATOS
INFORMADOS PELO PACIENTE. O sistema não diagnostica, não afirma doença,
não determina emergência e não atribui prioridade clínica automaticamente.
"""

import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from App.core.database import Base


class CareRequestStatus(str, enum.Enum):
    """Status operacionais da solicitação de atendimento (MED V3)."""

    CREATED = "CREATED"
    IN_REVIEW = "IN_REVIEW"
    REFERRED = "REFERRED"
    SCHEDULED = "SCHEDULED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class CareRequest(Base):
    """Solicitação de atendimento criada pelo paciente (MED V3)."""

    __tablename__ = "care_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=False
    )
    reason: Mapped[str] = mapped_column(String(500), nullable=False)  # motivo
    specialty: Mapped[str] = mapped_column(String(100), nullable=False)  # especialidade desejada
    symptoms: Mapped[str] = mapped_column(Text, default="", nullable=False)  # sintomas relatados
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)  # descrição da situação
    cep: Mapped[str] = mapped_column(String(9), nullable=False)  # CEP/localização
    referral: Mapped[str] = mapped_column(String(500), default="", nullable=False)  # encaminhamento médico (opcional)
    discomfort_level: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-10, informado pelo paciente
    symptom_onset: Mapped[date] = mapped_column(Date, nullable=False)  # data de início dos sintomas
    notes: Mapped[str] = mapped_column(String(500), default="", nullable=False)  # observações
    status: Mapped[CareRequestStatus] = mapped_column(
        Enum(CareRequestStatus, name="care_request_status"),
        default=CareRequestStatus.CREATED,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
