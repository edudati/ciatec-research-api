"""F6-02: questionnaire_responses and question_answers.

Revision ID: f6_02_questionnaire_responses
Revises: f6_01_assessment_records
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f6_02_questionnaire_responses"
down_revision: str | Sequence[str] | None = "f6_01_assessment_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "questionnaire_responses",
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
            "questionnaire_template_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "executor_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.CheckConstraint(
            "status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED')",
            name="ck_questionnaire_responses_status",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_questionnaire_responses_project_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["participant_profile_id"],
            ["participant_profiles.id"],
            name="fk_questionnaire_responses_participant_profile_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["questionnaire_template_id"],
            ["questionnaire_templates.id"],
            name="fk_questionnaire_responses_questionnaire_template_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["executor_id"],
            ["users.id"],
            name="fk_questionnaire_responses_executor_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_questionnaire_responses_project_id",
        "questionnaire_responses",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_questionnaire_responses_participant_profile_id",
        "questionnaire_responses",
        ["participant_profile_id"],
        unique=False,
    )
    op.create_index(
        "ix_questionnaire_responses_questionnaire_template_id",
        "questionnaire_responses",
        ["questionnaire_template_id"],
        unique=False,
    )

    op.create_table(
        "question_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "questionnaire_response_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "question_item_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "value",
            postgresql.JSONB(astext_type=sa.Text()),
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
            ["questionnaire_response_id"],
            ["questionnaire_responses.id"],
            name="fk_question_answers_questionnaire_response_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["question_item_id"],
            ["question_items.id"],
            name="fk_question_answers_question_item_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "questionnaire_response_id",
            "question_item_id",
            name="uq_question_answers_response_item",
        ),
    )
    op.create_index(
        "ix_question_answers_questionnaire_response_id",
        "question_answers",
        ["questionnaire_response_id"],
        unique=False,
    )
    op.create_index(
        "ix_question_answers_question_item_id",
        "question_answers",
        ["question_item_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_question_answers_question_item_id", table_name="question_answers")
    op.drop_index(
        "ix_question_answers_questionnaire_response_id",
        table_name="question_answers",
    )
    op.drop_table("question_answers")
    op.drop_index(
        "ix_questionnaire_responses_questionnaire_template_id",
        table_name="questionnaire_responses",
    )
    op.drop_index(
        "ix_questionnaire_responses_participant_profile_id",
        table_name="questionnaire_responses",
    )
    op.drop_index(
        "ix_questionnaire_responses_project_id",
        table_name="questionnaire_responses",
    )
    op.drop_table("questionnaire_responses")
