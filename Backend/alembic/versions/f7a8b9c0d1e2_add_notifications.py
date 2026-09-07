"""MED V7: notifications table

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-02-22
"""

from alembic import op
import sqlalchemy as sa

revision = "f7a8b9c0d1e2"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column(
            "type",
            sa.Enum(
                "CARE_REQUEST_CREATED", "CARE_REQUEST_RECEIVED", "QUEUE_POSITION_CHANGED",
                "QUEUE_PRIORITY_CHANGED", "CARE_REQUEST_REFERRED", "APPOINTMENT_AVAILABLE",
                "APPOINTMENT_SCHEDULED", "APPOINTMENT_CANCELLED", "APPOINTMENT_RESCHEDULED",
                "PATIENT_STATUS_UPDATED", "MEDICAL_EVALUATION_CREATED", "DOCUMENT_RECEIVED",
                name="notification_type",
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("related_resource_type", sa.String(length=50), nullable=True),
        sa.Column("related_resource_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notifications_user_created", "notifications", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_created", table_name="notifications")
    op.drop_table("notifications")
    sa.Enum(name="notification_type").drop(op.get_bind(), checkfirst=True)
