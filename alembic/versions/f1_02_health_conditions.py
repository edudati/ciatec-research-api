"""Health conditions repository + minimal participant_conditions (F1-02).

Revision ID: f1_02_health_conditions
Revises: f1_01_participant_profiles

`participant_conditions` is minimal here so soft-delete can be blocked when
in use; F1-03 will add temporal/severity columns via a follow-up migration.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f1_02_health_conditions"
down_revision: str | Sequence[str] | None = "f1_01_participant_profiles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "health_conditions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_health_conditions_code"),
    )
    op.create_index(
        "ix_health_conditions_category",
        "health_conditions",
        ["category"],
        unique=False,
    )

    op.create_table(
        "participant_conditions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "participant_profile_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "health_condition_id",
            postgresql.UUID(as_uuid=True),
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
        sa.ForeignKeyConstraint(
            ["health_condition_id"],
            ["health_conditions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["participant_profile_id"],
            ["participant_profiles.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_participant_conditions_health_condition_id",
        "participant_conditions",
        ["health_condition_id"],
        unique=False,
    )
    op.create_index(
        "ix_participant_conditions_participant_profile_id",
        "participant_conditions",
        ["participant_profile_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("participant_conditions")
    op.drop_table("health_conditions")
