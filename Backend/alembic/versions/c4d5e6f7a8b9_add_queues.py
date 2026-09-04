"""MED V4: queues + queue_events tables

Revision ID: c4d5e6f7a8b9
Revises: b7c8d9e0f1a2
Create Date: 2026-02-21
"""

from alembic import op
import sqlalchemy as sa

revision = "c4d5e6f7a8b9"
down_revision = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "queues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("care_request_id", sa.Integer(), sa.ForeignKey("care_requests.id"), nullable=False, index=True),
        sa.Column("specialty", sa.String(length=100), nullable=False),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("WAITING", "IN_REVIEW", "REFERRED", "SCHEDULED", "REMOVED", "COMPLETED", name="queue_status"),
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.Enum("NORMAL", "MEDIUM", "HIGH", "URGENT", name="queue_priority"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("entered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_queues_specialty_status", "queues", ["specialty", "status"])

    op.create_table(
        "queue_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("queue_id", sa.Integer(), sa.ForeignKey("queues.id"), nullable=False, index=True),
        sa.Column(
            "event_type",
            sa.Enum(
                "CREATED",
                "POSITION_CHANGED",
                "PRIORITY_CHANGED",
                "STATUS_CHANGED",
                "REFERRED",
                "REMOVED",
                name="queue_event_type",
            ),
            nullable=False,
        ),
        sa.Column("previous_position", sa.Integer(), nullable=True),
        sa.Column("new_position", sa.Integer(), nullable=True),
        sa.Column("previous_priority", sa.Enum("NORMAL", "MEDIUM", "HIGH", "URGENT", name="queue_priority"), nullable=True),
        sa.Column("new_priority", sa.Enum("NORMAL", "MEDIUM", "HIGH", "URGENT", name="queue_priority"), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("queue_events")
    op.drop_index("ix_queues_specialty_status", table_name="queues")
    op.drop_table("queues")
    sa.Enum(name="queue_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="queue_event_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="queue_priority").drop(op.get_bind(), checkfirst=True)
