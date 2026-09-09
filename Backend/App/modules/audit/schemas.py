"""MED V10 — Schemas Pydantic da auditoria (contratos HTTP de entrada/saída)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditLogRead(BaseModel):
    """Representação de saída de um registro de auditoria."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: int | None
    actor_role: str | None
    action: str
    resource_type: str
    resource_id: int | None
    # Valores chegam como JSON TEXT no banco; aqui viram objeto novamente
    # para o cliente não precisar fazer double-parse.
    previous_value: dict[str, Any] | None = None
    new_value: dict[str, Any] | None = None
    created_at: datetime


class AuditLogList(BaseModel):
    """Envelope paginado — contrato único de paginação do projeto (V10+).

    Page-based (page/page_size + total): listagem de auditoria é navegação
    humana em ordem cronológica; o total permite "X de Y" na UI.
    """

    items: list[AuditLogRead]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
