"""MED V10 — Helpers de integração da auditoria com os fluxos existentes.

Assim como `notifications/events.py` (V7), este módulo concentra os pontos de
emissão para que os services de negócio não dependam diretamente do
AuditService — apenas de funções explícitas e nomeadas por evento.
"""

from typing import Any

from sqlalchemy.orm import Session

from App.modules.audit.service import AuditService
from App.modules.audit.models import AuditAction


def audit_create(
    db: Session,
    resource_type: str,
    resource_id: int,
    actor_id: int | None = None,
    actor_role: str | None = None,
    new_value: dict[str, Any] | None = None,
) -> None:
    """Helper para eventos de criação (fluentíssimo de chamar dos services)."""
    AuditService(db).log(
        action=AuditAction.CREATE,
        resource_type=resource_type,
        resource_id=resource_id,
        actor_id=actor_id,
        actor_role=actor_role,
        new_value=new_value,
    )


def audit_update(
    db: Session,
    resource_type: str,
    resource_id: int,
    actor_id: int | None = None,
    actor_role: str | None = None,
    previous_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
) -> None:
    """Helper para eventos de atualização (guarda antes/depois)."""
    AuditService(db).log(
        action=AuditAction.UPDATE,
        resource_type=resource_type,
        resource_id=resource_id,
        actor_id=actor_id,
        actor_role=actor_role,
        previous_value=previous_value,
        new_value=new_value,
    )
