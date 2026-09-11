#
# ÁREA: MÓDULO AUDIT — MODELS (audit/models.py)
# Tabela `audit_logs`: registro imutável (append-only) de quem fez o quê.
#
"""MED V10 — Modelo de auditoria.

Responsabilidade:
- Registrar quem (actor) fez o quê (action) em qual recurso (resource),
  com valores anteriores/novos e timestamp, de forma IMUTÁVEL (append-only).

Decisões arquiteturais:
- Append-only: nenhuma operação da aplicação atualiza ou apaga linhas de
  auditoria. O histórico é a fonte de verdade para revisão e conformidade.
- NUNCA registrar secrets (senha, token, chave). O service filtra campos
  sensíveis antes de persistir — ver `audit/service.py`.
- previous_value/new_value são TEXT (JSON serializado): a auditoria precisa
  ser robusta a mudanças de schema — um snapshot textual não quebra quando
  um campo muda de tipo nas versões futuras.
- FK do actor é SET NULL: se um usuário for removido, o registro de auditoria
  continua existindo (dados históricos não podem desaparecer com a pessoa).
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from App.core.database import Base


class AuditAction(str, enum.Enum):
    """Ações auditáveis (grupo mínimo da V10, extensível)."""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"


class AuditLog(Base):
    """Registro imutável de uma ação relevante do sistema."""

    __tablename__ = "audit_logs"
    # Índice composto: a consulta dominante é "ações mais recentes" e
    # "ações de um ator em ordem cronológica" (lista paginada da V10/V11).
    __table_args__ = (
        Index("ix_audit_logs_created_at", "created_at"),
        Index("ix_audit_logs_actor_created", "actor_id", "created_at"),
        # Índice V11: auditoria por recurso auditado ("quem mexeu no queue 7?").
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Actor é opcional: eventos de sistema (sem usuário humano) também são auditados.
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    # Papel do ator congelado no momento do evento: se o papel do usuário mudar
    # depois, o histórico continua fiel ao que ele era quando agiu.
    actor_role: Mapped[str | None] = mapped_column(String(20), nullable=True)
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction, name="audit_action"), nullable=False)
    # Recurso auditado em pares (tipo, id) — sem FK: recursos de tipos distintos
    # (care_request, queue, appointment...) vivem em tabelas diferentes e uma FK
    # polimórfica não é possível no PostgreSQL sem anti-patterns.
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    previous_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
