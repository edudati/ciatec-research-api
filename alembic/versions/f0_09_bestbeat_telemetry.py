"""Bestbeat telemetry tables (F0-09).

Revision ID: f0_09_bestbeat_telemetry
Revises: f0_08_bubbles_telemetry
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f0_09_bestbeat_telemetry"
down_revision: str | Sequence[str] | None = "f0_08_bubbles_telemetry"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "bestbeat_world",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp_ms", sa.BigInteger(), nullable=False),
        sa.Column("device", sa.String(length=256), nullable=False),
        sa.Column(
            "data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "match_id",
            "timestamp_ms",
            "device",
            name="uq_bestbeat_world_match_ts_device",
        ),
    )
    op.create_index(
        op.f("ix_bestbeat_world_match_id"),
        "bestbeat_world",
        ["match_id"],
        unique=False,
    )

    op.create_table(
        "bestbeat_pose",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp_ms", sa.BigInteger(), nullable=False),
        sa.Column(
            "data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "match_id",
            "timestamp_ms",
            name="uq_bestbeat_pose_match_ts",
        ),
    )
    op.create_index(
        op.f("ix_bestbeat_pose_match_id"),
        "bestbeat_pose",
        ["match_id"],
        unique=False,
    )

    op.create_table(
        "bestbeat_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("timestamp_ms", sa.BigInteger(), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_bestbeat_events_match_id"),
        "bestbeat_events",
        ["match_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_bestbeat_events_match_id"), table_name="bestbeat_events")
    op.drop_table("bestbeat_events")
    op.drop_index(op.f("ix_bestbeat_pose_match_id"), table_name="bestbeat_pose")
    op.drop_table("bestbeat_pose")
    op.drop_index(op.f("ix_bestbeat_world_match_id"), table_name="bestbeat_world")
    op.drop_table("bestbeat_world")
