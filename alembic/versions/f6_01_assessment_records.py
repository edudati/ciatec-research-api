"""F6-01: assessment_records (clinical assessment instances per project).

Revision ID: f6_01_assessment_records
Revises: f5_04_instrument_indications
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f6_01_assessment_records"
down_revision: str | Sequence[str] | None = "f5_04_instrument_indications"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assessment_records",
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
            "template_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "executor_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("score", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column(
            "data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
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
            name="fk_assessment_records_project_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["participant_profile_id"],
            ["participant_profiles.id"],
            name="fk_assessment_records_participant_profile_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["assessment_templates.id"],
            name="fk_assessment_records_template_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["executor_id"],
            ["users.id"],
            name="fk_assessment_records_executor_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_assessment_records_project_id",
        "assessment_records",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_assessment_records_participant_profile_id",
        "assessment_records",
        ["participant_profile_id"],
        unique=False,
    )
    op.create_index(
        "ix_assessment_records_template_id",
        "assessment_records",
        ["template_id"],
        unique=False,
    )
    op.create_index(
        "ix_assessment_records_performed_at",
        "assessment_records",
        ["performed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_assessment_records_performed_at", table_name="assessment_records")
    op.drop_index("ix_assessment_records_template_id", table_name="assessment_records")
    op.drop_index(
        "ix_assessment_records_participant_profile_id",
        table_name="assessment_records",
    )
    op.drop_index("ix_assessment_records_project_id", table_name="assessment_records")
    op.drop_table("assessment_records")
