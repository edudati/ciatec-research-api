"""F3-02: project groups + minimal participant_enrollments for delete guard.

Revision ID: f3_02_groups
Revises: f3_01_projects
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f3_02_groups"
down_revision: str | Sequence[str] | None = "f3_01_projects"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
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
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_groups_project_id", "groups", ["project_id"], unique=False)
    op.execute(
        "CREATE UNIQUE INDEX uq_groups_project_name_ci "
        "ON groups (project_id, (lower(btrim(name))))",
    )

    op.create_table(
        "participant_enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "participant_profile_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "group_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column(
            "enrolled_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("exited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "enrolled_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
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
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["participant_profile_id"],
            ["participant_profiles.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["groups.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["enrolled_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_participant_enrollments_project_id",
        "participant_enrollments",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_participant_enrollments_group_id",
        "participant_enrollments",
        ["group_id"],
        unique=False,
    )
    op.create_index(
        "ix_participant_enrollments_profile_id",
        "participant_enrollments",
        ["participant_profile_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_participant_enrollments_profile_id",
        table_name="participant_enrollments",
    )
    op.drop_index(
        "ix_participant_enrollments_group_id",
        table_name="participant_enrollments",
    )
    op.drop_index(
        "ix_participant_enrollments_project_id",
        table_name="participant_enrollments",
    )
    op.drop_table("participant_enrollments")
    op.execute("DROP INDEX IF EXISTS uq_groups_project_name_ci")
    op.drop_index("ix_groups_project_id", table_name="groups")
    op.drop_table("groups")
