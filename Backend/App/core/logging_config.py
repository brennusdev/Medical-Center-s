"""MED V12 — Logging estruturado.

Responsabilidade:
- Formato JSON de uma linha por evento (parseável por qualquer coletor):
  nível, timestamp, módulo, evento e, quando disponível, request_id.

Diferença Application Log vs Audit Log (documentação V12):
- Application Log (este módulo): diagnóstico TÉCNICO e volátil — erros,
  latência, inicialização. Nunca substitui auditoria.
- Audit Log (App/modules/audit, V10): registro de NEGÓCIO persistido no
  banco ("quem fez o quê"), permanente e consultável via API.

Segurança:
- Nenhum logger do Med registra senha, token, secret ou payload completo
  de requisições (dados clínicos). Mensagens são eventos + identificadores.
"""

import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Formata registros como JSON de uma linha (stdout — padrão de containers)."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "event": record.getMessage(),
        }
        # request_id chega via `extra={"request_id": ...}` quando existe.
        request_id = getattr(record, "request_id", None)
        if request_id:
            payload["request_id"] = request_id
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: int = logging.INFO) -> None:
    """Configura o logging raiz do Med (chamado uma vez no startup da API/worker)."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Logger padronizado por módulo (ex.: get_logger('med.api'))."""
    return logging.getLogger(name)
