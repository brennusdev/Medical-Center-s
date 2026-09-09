"""MED V10 — Camada de acesso a dados da auditoria (sem regras de negócio).

Somente INSERT e SELECT: auditoria é append-only. Não existem métodos de
update/delete por decisão de segurança — nem por engano um fluxo futuro deve
alterar o histórico.
"""

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from App.modules.audit.models import AuditAction, AuditLog


class AuditRepository:
    """Único ponto de acesso ao banco para audit_logs."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, log: AuditLog) -> AuditLog:
        """Persiste um registro de auditoria.

        O commit fica aqui (padrão dos repositories do projeto): a auditoria
        é uma transação própria e best-effort — uma falha de auditoria nunca
        deve quebrar o fluxo de negócio que a gerou (ver service).
        """
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def list_logs(
        self,
        actor_id: int | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
        action: AuditAction | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Lista paginada (OFFSET) com filtros opcionais.

        Paginação por offset/limit: a listagem de auditoria é navegação humana
        com ordenação por created_at (indexado em ix_audit_logs_created_at);
        offsets moderados são baratos e a API é simples e estável. Para
        deep-pagination de bilhões de linhas, keyset seria melhor — documentado
        na V11 (estratégia por recurso).
        """
        stmt = select(AuditLog)
        if actor_id is not None:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        if resource_type is not None:
            stmt = stmt.where(AuditLog.resource_type == resource_type)
        if resource_id is not None:
            stmt = stmt.where(AuditLog.resource_id == resource_id)
        if action is not None:
            stmt = stmt.where(AuditLog.action == action)
        # Ordenação no banco (created_at desc, id desc como desempate estável —
        # created_at sozinho pode empatar no mesmo segundo).
        stmt = stmt.order_by(desc(AuditLog.created_at), desc(AuditLog.id)).limit(limit).offset(offset)
        return list(self.db.scalars(stmt).all())

    def get(self, log_id: int) -> AuditLog | None:
        return self.db.get(AuditLog, log_id)
