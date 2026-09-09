"""MED V11: advanced database — constraints and indexes.

Revision ID: c1d2e3f4a5b6
Revises: b0c1d2e3f4a5
Create Date: 2026-02-23

DECISÕES (documentação obrigatória da V11):

CONSTRAINTS — integridade no banco quando a regra é de DADOS (não de domínio):
- check_patient_status_severity 0..10: a escala é subjetiva, mas o DOMÍNIO é
  fixo. Garantir no banco protege contra qualquer fluxo futuro que esqueça a
  validação do Pydantic (ex.: script de manutenção).
- check_care_discomfort 1..10: idem, faixa fixa do relato.
- check_queue_position_positive: posição 0 ou negativa corromperia a
  ordenação determinística da fila (invariante estrutural, não regra clínica).
- índice único users.email: já existia no model (unique=True); aqui é
  materializado como constraint nomeada (uc_users_email) no Postgres.

FOREIGN KEYS — política ON DELETE:
- care_requests.patient_id → users.id: RESTRICT (NOC ACTION). Excluir um
  usuário com histórico de atendimentos destruiria registros clínicos.
- patient_status_updates.care_request_id → RESTRICT: relato é histórico.
- queues.care_request_id → RESTRICT: fila referencia solicitação viva.
- Em SQLite (ambiente de desenvolvimento/testes) FKs só são ativas com
  PRAGMA foreign_keys=ON; a migration usa batch_alter_table para portabilidade.

INDEXES — somente os que atendem consultas reais do projeto:
- ix_care_requests_specialty: filtro de especialidade no analytics (V8).
- ix_queues_status_position: listagem ativa ordenada por posição.
- ix_queue_events_created_at: timeline ordenada cronologicamente.
- ix_notifications_created_at: listagem paginada global recente.
- ix_audit_logs_resource: auditoria por recurso (tipo, id).
Índices custam em todo INSERT/UPDATE; nenhum foi criado "por precaução".
"""

from alembic import op
import sqlalchemy as sa

revision = "c1d2e3f4a5b6"
down_revision = "b0c1d2e3f4a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Constraints de domínio numérico (check) -----------------------------
    # batch_alter_table: necessário para SQLite, inofensivo para Postgres —
    # recria a tabela em SQLite (que não suporta ALTER ADD CONSTRAINT).
    with op.batch_alter_table("patient_status_updates") as batch:
        batch.create_check_constraint(
            "ck_patient_status_severity_range", "severity >= 0 AND severity <= 10"
        )
    with op.batch_alter_table("care_requests") as batch:
        batch.create_check_constraint(
            "ck_care_requests_discomfort_range", "discomfort_level >= 1 AND discomfort_level <= 10"
        )
    with op.batch_alter_table("queues") as batch:
        batch.create_check_constraint("ck_queues_position_positive", "position >= 1")

    # -- Índices de consulta (cada um justificado no docstring) ---------------
    op.create_index("ix_care_requests_specialty", "care_requests", ["specialty"])
    op.create_index("ix_queues_status_position", "queues", ["status", "position"])
    op.create_index("ix_queue_events_created_at", "queue_events", ["created_at"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])
    op.create_index("ix_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"])

    # -- Unicidade explícita de email (constraint nomeada) --------------------
    # SQLite ignora nomes de unique constraints em batch (recria a tabela);
    # no Postgres o nome estável permite drop limpo no downgrade.
    with op.batch_alter_table("users") as batch:
        batch.create_unique_constraint("uc_users_email", ["email"])


def downgrade() -> None:
    # Ordem inversa, segura: nada aqui referencia objetos de outras versões.
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("uc_users_email", type_="unique")
    op.drop_index("ix_audit_logs_resource", table_name="audit_logs")
    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_queue_events_created_at", table_name="queue_events")
    op.drop_index("ix_queues_status_position", table_name="queues")
    op.drop_index("ix_care_requests_specialty", table_name="care_requests")
    with op.batch_alter_table("queues") as batch:
        batch.drop_constraint("ck_queues_position_positive", type_="check")
    with op.batch_alter_table("care_requests") as batch:
        batch.drop_constraint("ck_care_requests_discomfort_range", type_="check")
    with op.batch_alter_table("patient_status_updates") as batch:
        batch.drop_constraint("ck_patient_status_severity_range", type_="check")
