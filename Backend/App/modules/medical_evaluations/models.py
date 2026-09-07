"""MED V6 — SQLAlchemy model for professional medical evaluations.

REGRAS DE SEGURANÇA (obrigatórias):
- `evaluation` e `recommendation` são AVALIAÇÃO PROFISSIONAL registrada por um
  usuário autorizado — nunca geradas automaticamente pelo sistema.
- O RELATO DO PACIENTE (PatientStatusUpdate) permanece intacto: a avaliação
  referencia o relato, nunca o sobrescreve.
- Sem IA, sem diagnóstico automático, sem RBAC completo (compatível com V9).
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from App.core.database import Base


class MedicalEvaluation(Base):
    """Avaliação profissional sobre uma atualização de estado do paciente (MED V6)."""

    __tablename__ = "medical_evaluations"
    __table_args__ = (
        Index("ix_medical_eval_care_request_created", "care_request_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_status_update_id: Mapped[int] = mapped_column(
        ForeignKey("patient_status_updates.id"), index=True, nullable=False
    )
    care_request_id: Mapped[int] = mapped_column(
        ForeignKey("care_requests.id"), index=True, nullable=False
    )
    # Profissional responsável (registro de auditoria); papel validado no service.
    professional_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=False
    )
    evaluation: Mapped[str] = mapped_column(Text, nullable=False)  # texto livre do profissional
    recommendation: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    # Ligação opcional com a fila, quando a avaliação resultar em ação operacional.
    queue_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # sem FK: Queue pode estar em outra especialidade/contexto
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    patient_status_update = relationship("PatientStatusUpdate", viewonly=True)
    care_request = relationship("CareRequest", viewonly=True)
    professional = relationship("User", viewonly=True)


# Papéis autorizados a criar avaliações (estrutura simples, compatível com RBAC futuro).
AUTHORIZED_ROLES = ("RECEPTIONIST", "NURSE", "DOCTOR", "HOSPITAL", "ADMIN")
