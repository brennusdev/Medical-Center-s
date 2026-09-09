"""MED V10: audit_logs table (append-only).

Revision ID: b0c1d2e3f4a5
Revises: a8b9c0d1e2f3
Create Date: 2026-02-23

Decisões:
- Tabela nova (nada de versões anteriores é alterado).
- actor_id com ON DELETE SET NULL: histórico de auditoria sobrevive à
  remoção do usuário (dados de conformidade nunca desaparecem).
"""

from alembic import op
import sqlalchemy as sa

revision = "b0c1d2e3f4a5"
down_revision = "a8b9c0d1e2f3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "actor_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("actor_role", sa.String(length=20), nullable=True),
        sa.Column(
            "action",
            sa.Enum("CREATE", "UPDATE", "DELETE", "LOGIN", name="audit_action"),
            nullable=False,
        ),
        sa.Column("resource_type", sa.String(length=50), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=True, index=True),
        sa.Column("previous_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    # Índices: lista paginada por data e filtro por ator em ordem cronológica.
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_actor_created", "audit_logs", ["actor_id", "created_at"])


def downgrade() -> None:
    # Downgrade seguro: a tabela é exclusiva da V10 e não é referenciada.
    op.drop_index("ix_audit_logs_actor_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_table("audit_logs")
    sa.Enum(name="audit_action").drop(op.get_bind(), checkfirst=True)
