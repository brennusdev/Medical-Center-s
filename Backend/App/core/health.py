"""MED V11 — Database health check.

Responsabilidade:
- Verificar conectividade REAL com o banco com o menor custo possível
  (`SELECT 1`), para uso interno (health/readiness da V12, workers, CI).

Segurança:
- NUNCA expor credenciais, host, string de conexão ou nome do banco.
  A resposta é booleana + latência em ms — nada mais. Um erro de conexão
  é logado (application log) sem detalhes sensíveis no payload.
"""

import logging
import time

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger("med.db")


def check_database(db: Session) -> dict:
    """Executa `SELECT 1` e mede a latência.

    Retorno estável (contrato consumido por readiness/liveness da V12):
    {"ok": bool, "latency_ms": float | None}
    """
    start = time.perf_counter()
    try:
        db.execute(text("SELECT 1"))
        latency = round((time.perf_counter() - start) * 1000, 2)
        return {"ok": True, "latency_ms": latency}
    except Exception:  # noqa: BLE001 — health check nunca deve propagar exceção
        logger.exception("Database health check falhou")
        return {"ok": False, "latency_ms": None}
