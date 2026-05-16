"""F6-03: intervention_records (clinical intervention instances per project).

Revision ID: f6_03_intervention_records
Revises: f6_02_questionnaire_responses
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f6_03_intervention_records"
down_revision: str | Sequence[str] | None = "f6_02_questionnaire_responses"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "intervention_records",
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
        sa.Column(
            "match_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
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
            name="fk_intervention_records_project_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["participant_profile_id"],
            ["participant_profiles.id"],
            name="fk_intervention_records_participant_profile_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["intervention_templates.id"],
            name="fk_intervention_records_template_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["executor_id"],
            ["users.id"],
            name="fk_intervention_records_executor_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["match_id"],
            ["matches.id"],
            name="fk_intervention_records_match_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "match_id",
            name="uq_intervention_records_match_id",
        ),
    )
    op.create_index(
        "ix_intervention_records_project_id",
        "intervention_records",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_intervention_records_participant_profile_id",
        "intervention_records",
        ["participant_profile_id"],
        unique=False,
    )
    op.create_index(
        "ix_intervention_records_template_id",
        "intervention_records",
        ["template_id"],
        unique=False,
    )
    op.create_index(
        "ix_intervention_records_performed_at",
        "intervention_records",
        ["performed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_intervention_records_performed_at",
        table_name="intervention_records",
    )
    op.drop_index(
        "ix_intervention_records_template_id",
        table_name="intervention_records",
    )
    op.drop_index(
        "ix_intervention_records_participant_profile_id",
        table_name="intervention_records",
    )
    op.drop_index(
        "ix_intervention_records_project_id",
        table_name="intervention_records",
    )
    op.drop_table("intervention_records")
