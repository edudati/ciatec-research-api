"""F9-01: self_report_tokens for participant fill links.

Revision ID: f9_01_self_report_tokens
Revises: f8_01_sessions_enrollment_id
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f9_01_self_report_tokens"
down_revision: str | Sequence[str] | None = "f8_01_sessions_enrollment_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "self_report_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "response_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("token", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["response_id"],
            ["questionnaire_responses.id"],
            name="fk_self_report_tokens_response_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "response_id",
            name="uq_self_report_tokens_response_id",
        ),
        sa.UniqueConstraint(
            "token",
            name="uq_self_report_tokens_token",
        ),
    )


def downgrade() -> None:
    op.drop_table("self_report_tokens")
