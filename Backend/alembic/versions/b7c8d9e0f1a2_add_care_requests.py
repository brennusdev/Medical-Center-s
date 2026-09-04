"""MED V3: care_requests table + users.role column

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-02-20
"""

from alembic import op
import sqlalchemy as sa

revision = "b7c8d9e0f1a2"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Coluna aditiva na V1 (users): papel do usuário, preservando dados existentes.
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=20), nullable=False, server_default="PATIENT"),
    )

    op.create_table(
        "care_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("specialty", sa.String(length=100), nullable=False),
        sa.Column("symptoms", sa.Text(), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("cep", sa.String(length=9), nullable=False),
        sa.Column("referral", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("discomfort_level", sa.Integer(), nullable=False),
        sa.Column("symptom_onset", sa.Date(), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=False, server_default=""),
        sa.Column(
            "status",
            sa.Enum(
                "CREATED",
                "IN_REVIEW",
                "REFERRED",
                "SCHEDULED",
                "CANCELLED",
                "COMPLETED",
                name="care_request_status",
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("care_requests")
    sa.Enum(name="care_request_status").drop(op.get_bind(), checkfirst=True)
    op.drop_column("users", "role")
