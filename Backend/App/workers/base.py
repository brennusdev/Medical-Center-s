"""MED V12 — Infraestrutura de processamento assíncrono (workers).

Responsabilidade:
- Fornecer uma abstração SIMPLES de fila de tarefas internas, sem dependências
  externas (Celery/Kafka) nesta etapa. A notificação da V7 já é best-effort;
  este módulo é o ponto de extensão documentado para movê-la (e tarefas
  demoradas/analytics pesados) para fora do ciclo request/response.

Quando usar worker x chamada síncrona (decisão arquitetural):
- SÍNCRONO: tudo que a resposta HTTP depende do resultado (regras de fila,
  agendamento, autenticação). O Med é transacional e consistency-first.
- WORKER (futuro): notificações por e-mail/push, exportações, reprocessamento
  analítico — tarefas onde atraso é aceitável e retrabalho é seguro.

PostgreSQL x Redis (quando usar cada um):
- PostgreSQL: fonte da verdade, dados clínicos, filas de atendimento,
  auditoria — exige transações e integridade referencial.
- Redis: cache efêmero, filas internas de trabalho, contadores — perde-se
  nada crítico se esvaziar. NUNCA persistir dado clínico somente no Redis.
"""
from __future__ import annotations

import logging
import time
from typing import Callable

from App.core.logging_config import get_logger

logger = get_logger("med.worker")


class TaskQueue:
    """Fila em memória com processamento em loop (abstração da V12).

    Por que em memória e não Redis ainda? A V12 PREPARA a infraestrutura:
    trocar esta implementação por uma fila Redis mantém o contrato
    (`enqueue`/`run_forever`) sem alterar quem publica tarefas — o custo
    de uma fila real só se paga quando houver múltiplos processos worker.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, Callable[[dict], None]] = {}

    def register(self, name: str, handler: Callable[[dict], None]) -> None:
        """Registra o handler de um tipo de tarefa (ex.: 'send_notification')."""
        self._handlers[name] = handler

    def enqueue(self, name: str, payload: dict) -> None:
        """Publica uma tarefa. Em produção, substituir por push no Redis."""
        handler = self._handlers.get(name)
        if handler is None:
            # Erro de programação, não de runtime: falhar cedo e alto.
            raise KeyError(f"Task '{name}' sem handler registrado")
        try:
            handler(payload)
        except Exception:  # noqa: BLE001 — worker nunca deve morrer por 1 tarefa
            # Log sem payload: pode conter dado clínico/sensível.
            logger.exception("Task '%s' falhou", name)


def run_forever(poll_seconds: float = 5.0) -> None:
    """Loop principal do worker standalone (`python -m App.workers.base`).

    Mantém o processo vivo (orquestradores reiniciam se sair) e processa
    tarefas. Hoje não há fila persistida: o loop existe para o healthcheck
    do container e para o ponto de extensão documentado.
    """
    logger.info("Worker iniciado (poll=%ss)", poll_seconds)
    queue = TaskQueue()
    while True:  # pragma: no cover — loop infinito por design
        time.sleep(poll_seconds)


if __name__ == "__main__":  # pragma: no cover
    run_forever()
