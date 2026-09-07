"""MED V9: users.password_hash (autenticação)

Revision ID: a8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-03-01

Migration ADITIVA: apenas acrescenta a coluna `password_hash` (nullable).
- Nullable de propósito: usuários criados antes da V9 ficam sem senha até
  passarem pelo fluxo de definição de senha. Nunca fazemos backfill de senha
  inventada (seria uma credencial conhecida/fracamente protegida).
- Nenhuma tabela existente é alterada ou apagada (regra do projeto).
"""
from alembic import op
import sqlalchemy as sa

revision = "a8b9c0d1e2f3"
down_revision = "f7a8b9c0d1e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "password_hash")
