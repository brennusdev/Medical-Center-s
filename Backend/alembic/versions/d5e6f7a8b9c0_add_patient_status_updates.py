"""MED V5: patient_status_updates table

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-02-22
"""

from alembic import op
import sqlalchemy as sa

revision = "d5e6f7a8b9c0"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patient_status_updates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("care_request_id", sa.Integer(), sa.ForeignKey("care_requests.id"), nullable=False, index=True),
        sa.Column(
            "state",
            sa.Enum("IMPROVED", "STABLE", "WORSENED", name="patient_state"),
            nullable=False,
        ),
        sa.Column("symptoms", sa.Text(), nullable=False, server_default=""),
        sa.Column("severity", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("notes", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_patient_status_care_request_created",
        "patient_status_updates",
        ["care_request_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_patient_status_care_request_created", table_name="patient_status_updates")
    op.drop_table("patient_status_updates")
    sa.Enum(name="patient_state").drop(op.get_bind(), checkfirst=True)
