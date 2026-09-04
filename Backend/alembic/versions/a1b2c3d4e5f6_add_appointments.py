"""MED V2: appointments and appointment requests

Revision ID: a1b2c3d4e5f6
Revises: 0001
Create Date: 2026-02-12
"""

from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "appointment_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), nullable=False, index=True),
        sa.Column("specialty", sa.String(length=100), nullable=False),
        sa.Column("preferred_date", sa.Date(), nullable=False),
        sa.Column("preferred_time", sa.Time(), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False, server_default=""),
        sa.Column(
            "status",
            sa.Enum(
                "REQUESTED",
                "IN_REVIEW",
                "SCHEDULED",
                "CANCELLED",
                "EXPIRED",
                name="request_status",
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("appointment_requests.id"), nullable=False, index=True),
        sa.Column("patient_id", sa.Integer(), nullable=False, index=True),
        sa.Column("specialty", sa.String(length=100), nullable=False),
        sa.Column("doctor_name", sa.String(length=150), nullable=False),
        sa.Column("hospital_name", sa.String(length=150), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "SCHEDULED",
                "CONFIRMED",
                "CANCELLED",
                "COMPLETED",
                "EXPIRED",
                name="appointment_status",
            ),
            nullable=False,
        ),
        sa.Column("notes", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("appointments")
    op.drop_table("appointment_requests")
    sa.Enum(name="appointment_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="request_status").drop(op.get_bind(), checkfirst=True)
