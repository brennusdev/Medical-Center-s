"""MED V5 — SQLAlchemy model for patient status updates.

REGRAS DE SEGURANÇA (obrigatórias):
- state, symptoms, severity e description são RELATOS INFORMADOS PELO PACIENTE.
- O sistema NÃO diagnostica, NÃO interpreta severidade clinicamente, NÃO altera
  prioridade da fila e NÃO altera status da CareRequest a partir destes relatos.
- O histórico é append-only: cada atualização cria um novo registro, nunca
  sobrescreve o anterior.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from App.core.database import Base


class PatientState(str, enum.Enum):
    """Estado relatado pelo paciente (autoavaliação, não diagnóstico)."""

    IMPROVED = "IMPROVED"
    STABLE = "STABLE"
    WORSENED = "WORSENED"


class PatientStatusUpdate(Base):
    """Atualização periódica do estado informado pelo próprio paciente (MED V5)."""

    __tablename__ = "patient_status_updates"
    __table_args__ = (
        Index("ix_patient_status_care_request_created", "care_request_id", "created_at"),
        # MED V11 — faixa da escala subjetiva garantida no banco (0..10).
        CheckConstraint("severity >= 0 AND severity <= 10", name="ck_patient_status_severity_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=False
    )
    care_request_id: Mapped[int] = mapped_column(
        ForeignKey("care_requests.id"), index=True, nullable=False
    )
    state: Mapped[PatientState] = mapped_column(
        Enum(PatientState, name="patient_state"), nullable=False
    )
    symptoms: Mapped[str] = mapped_column(Text, default="", nullable=False)  # relato
    # Escala subjetiva 0-10 informada pelo paciente; NÃO é interpretada pelo sistema.
    severity: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)  # relato
    notes: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    patient = relationship("User", foreign_keys=[patient_id], viewonly=True)
    care_request = relationship("CareRequest", viewonly=True)
