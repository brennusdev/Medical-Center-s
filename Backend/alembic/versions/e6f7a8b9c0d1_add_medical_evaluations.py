"""MED V6: medical_evaluations table

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-02-22
"""

from alembic import op
import sqlalchemy as sa

revision = "e6f7a8b9c0d1"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "medical_evaluations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_status_update_id", sa.Integer(), sa.ForeignKey("patient_status_updates.id"), nullable=False, index=True),
        sa.Column("care_request_id", sa.Integer(), sa.ForeignKey("care_requests.id"), nullable=False, index=True),
        sa.Column("professional_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("evaluation", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("queue_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_medical_eval_care_request_created",
        "medical_evaluations",
        ["care_request_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_medical_eval_care_request_created", table_name="medical_evaluations")
    op.drop_table("medical_evaluations")
