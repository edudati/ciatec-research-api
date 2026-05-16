"""F4-01: enrollment exit_reason, uniqueness, timeline_events.

Revision ID: f4_01_enrollments_timeline
Revises: f3_03_project_members_user
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f4_01_enrollments_timeline"
down_revision: str | Sequence[str] | None = "f3_03_project_members_user"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "participant_enrollments",
        sa.Column("exit_reason", sa.Text(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_participant_enrollments_project_profile",
        "participant_enrollments",
        ["project_id", "participant_profile_id"],
    )

    op.create_table(
        "timeline_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "participant_profile_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "enrollment_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "executor_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "context",
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
        sa.ForeignKeyConstraint(
            ["participant_profile_id"],
            ["participant_profiles.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["enrollment_id"],
            ["participant_enrollments.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["executor_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_timeline_events_profile_occurred",
        "timeline_events",
        ["participant_profile_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_timeline_events_project_occurred",
        "timeline_events",
        ["project_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_timeline_events_enrollment_id",
        "timeline_events",
        ["enrollment_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_timeline_events_enrollment_id", table_name="timeline_events")
    op.drop_index("ix_timeline_events_project_occurred", table_name="timeline_events")
    op.drop_index("ix_timeline_events_profile_occurred", table_name="timeline_events")
    op.drop_table("timeline_events")
    op.drop_constraint(
        "uq_participant_enrollments_project_profile",
        "participant_enrollments",
        type_="unique",
    )
    op.drop_column("participant_enrollments", "exit_reason")
