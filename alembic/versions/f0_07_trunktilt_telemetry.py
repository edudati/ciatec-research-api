"""TrunkTilt telemetry tables + optional game slug (F0-07).

Revision ID: f0_07_trunktilt_telemetry
Revises: f0_05_sessions_matches
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f0_07_trunktilt_telemetry"
down_revision: str | Sequence[str] | None = "f0_05_sessions_matches"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "games",
        sa.Column("slug", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_games_slug",
        "games",
        ["slug"],
        unique=True,
        postgresql_where=sa.text("slug IS NOT NULL AND deleted_at IS NULL"),
    )

    op.create_table(
        "trunktilt_world",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("frame_id", sa.Integer(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ball_x", sa.Double(), nullable=True),
        sa.Column("ball_y", sa.Double(), nullable=True),
        sa.Column("ball_z", sa.Double(), nullable=True),
        sa.Column("plane_tilt_x", sa.Double(), nullable=True),
        sa.Column("plane_tilt_y", sa.Double(), nullable=True),
        sa.Column("virtual_input_x", sa.Double(), nullable=True),
        sa.Column("virtual_input_y", sa.Double(), nullable=True),
        sa.Column(
            "extras",
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
            "frame_id",
            name="uq_trunktilt_world_match_frame",
        ),
    )
    op.create_index(
        op.f("ix_trunktilt_world_match_id"),
        "trunktilt_world",
        ["match_id"],
        unique=False,
    )

    op.create_table(
        "trunktilt_pose",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("frame_id", sa.Integer(), nullable=False),
        sa.Column("landmark_id", sa.SmallInteger(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("visibility", sa.Double(), nullable=True),
        sa.Column("x", sa.Double(), nullable=True),
        sa.Column("y", sa.Double(), nullable=True),
        sa.Column("z", sa.Double(), nullable=True),
        sa.Column(
            "extras",
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
            "frame_id",
            "landmark_id",
            name="uq_trunktilt_pose_match_frame_landmark",
        ),
    )
    op.create_index(
        op.f("ix_trunktilt_pose_match_id"),
        "trunktilt_pose",
        ["match_id"],
        unique=False,
    )

    op.create_table(
        "trunktilt_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("match_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
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
        op.f("ix_trunktilt_events_match_id"),
        "trunktilt_events",
        ["match_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_trunktilt_events_match_id"), table_name="trunktilt_events")
    op.drop_table("trunktilt_events")
    op.drop_index(op.f("ix_trunktilt_pose_match_id"), table_name="trunktilt_pose")
    op.drop_table("trunktilt_pose")
    op.drop_index(op.f("ix_trunktilt_world_match_id"), table_name="trunktilt_world")
    op.drop_table("trunktilt_world")
    op.drop_index("ix_games_slug", table_name="games")
    op.drop_column("games", "slug")
