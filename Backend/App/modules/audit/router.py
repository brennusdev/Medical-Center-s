"""MED V10 — Rotas HTTP da auditoria (fins: ADMIN apenas).

Regra de negócio: auditoria é instrumento de governança — somente ADMIN lista.
Router é FINO: parsing, autorização e delegação ao service. Sem SQL aqui.
"""

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from App.core.database import get_db
from App.modules.audit.models import AuditAction
from App.modules.audit.schemas import AuditLogList, AuditLogRead
from App.modules.audit.service import AuditService
from App.modules.auth.dependencies import get_current_user
from App.modules.users.models import User

router = APIRouter(prefix="/audit", tags=["audit"])

# Papéis autorizados a consultar auditoria (V10). Mantido explícito e local:
# a matriz geral de permissões fica em auth/dependencies.py e pode absorver
# esta permissão depois sem mudar o contrato das rotas.
AUDIT_VIEW_ROLES = {"ADMIN"}


def _parse_json(raw: str | None) -> dict[str, Any] | None:
    """Converte o JSON TEXT do banco em objeto; dados legados/inválidos viram None."""
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return None


@router.get("/logs", response_model=AuditLogList)
def list_audit_logs(
    actor_id: int | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    resource_id: int | None = Query(default=None),
    action: AuditAction | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db=Depends(get_db),
    current_user: User | None = Depends(get_current_user),
) -> AuditLogList:
    """Lista paginada de eventos de auditoria.

    Paginação por page/page_size (page-based): escolhida aqui porque a
    listagem é navegação cronológica para humanos; keyset seria superior
    apenas para deep-pagination programática (decisão documentada na V11).
    """
    if current_user is not None and current_user.role not in AUDIT_VIEW_ROLES:
        # 403 (não 404): o recurso existe, o usuário é quem não pode vê-lo.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito a administradores.")

    offset = (page - 1) * page_size
    items = AuditService(db).list_logs(
        actor_id=actor_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        limit=page_size,
        offset=offset,
    )
    logs = [
        AuditLogRead(
            id=i.id,
            actor_id=i.actor_id,
            actor_role=i.actor_role,
            action=i.action.value if hasattr(i.action, "value") else str(i.action),
            resource_type=i.resource_type,
            resource_id=i.resource_id,
            previous_value=_parse_json(i.previous_value),
            new_value=_parse_json(i.new_value),
            created_at=i.created_at,
        )
        for i in items
    ]
    # total aproximado = posição do fim desta página; o total exato exigiria
    # um COUNT extra — mantemos simples enquanto page_size <= 100 limita o custo.
    return AuditLogList(items=logs, total=len(logs) + offset, page=page, page_size=page_size)
