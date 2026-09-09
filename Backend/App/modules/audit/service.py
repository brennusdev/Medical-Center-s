"""MED V10 — Service de auditoria.

Responsabilidades:
- Ser o PONTO ÚNICO de gravação de auditoria (nenhuma rota grava direto).
- Sanitizar payloads: campos sensíveis (senha, token, secret, chave) NUNCA
  entram no histórico — nem como valor novo nem como anterior.
- Ser best-effort: falha de auditoria nunca quebra o fluxo de negócio
  (mesma filosofia das notificações da V7).

Diferença Application Log vs Audit Log (documentada na V12):
- Application Log: diagnóstico técnico (erros, latência, request id) — volátil.
- Audit Log: registro de negócio persistido no banco ("quem fez o quê") —
  permanente, consultável via API.
"""

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from App.modules.audit.models import AuditAction, AuditLog
from App.modules.audit.repository import AuditRepository

logger = logging.getLogger("med.audit")

# Campos que jamais podem ser serializados para auditoria (nem mascarados):
# a presença deles no payload é irrelevante; o valor, perigoso.
SENSITIVE_KEYS = {"password", "password_hash", "token", "secret", "secret_key", "api_key", "authorization"}


def _sanitize(data: dict[str, Any] | None) -> str | None:
    """Serializa um snapshot para TEXT (JSON), removendo campos sensíveis.

    Campos sensíveis são REMOVIDOS (não mascarados) — mesmo um "***" indicaria
    que o campo existia e seu comprimento poderia vazar informação.
    """
    if not data:
        return None
    clean = {k: v for k, v in data.items() if k.lower() not in SENSITIVE_KEYS}
    if not clean:
        return None
    # default=str: datas/enums viram texto em vez de quebrar a serialização.
    return json.dumps(clean, default=str, ensure_ascii=False)


class AuditService:
    def __init__(self, db: Session) -> None:
        self.repo = AuditRepository(db)

    def log(
        self,
        action: AuditAction,
        resource_type: str,
        resource_id: int | None = None,
        actor_id: int | None = None,
        actor_role: str | None = None,
        previous_value: dict[str, Any] | None = None,
        new_value: dict[str, Any] | None = None,
    ) -> AuditLog | None:
        """Grava um evento de auditoria (best-effort).

        Por que best-effort? Auditoria é observação do fluxo, não parte da
        regra de negócio. Se o banco de auditoria falhar, o paciente continua
        sendo atendido; registramos em application log para investigação.
        """
        try:
            return self.repo.create(
                AuditLog(
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    actor_id=actor_id,
                    actor_role=actor_role,
                    previous_value=_sanitize(previous_value),
                    new_value=_sanitize(new_value),
                )
            )
        except Exception:  # noqa: BLE001 — intencional: nunca propagar falha de auditoria
            logger.exception("Falha ao registrar auditoria (best-effort)")
            return None

    def list_logs(self, **kwargs) -> list[AuditLog]:
        """Delegação paginada — validação de limites fica na camada de schemas."""
        return self.repo.list_logs(**kwargs)

    def get(self, log_id: int) -> AuditLog | None:
        return self.repo.get(log_id)
