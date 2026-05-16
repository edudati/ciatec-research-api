"""F8-01: optional enrollment_id on sessions (research gameplay context).

Revision ID: f8_01_sessions_enrollment_id
Revises: f6_03_intervention_records
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f8_01_sessions_enrollment_id"
down_revision: str | Sequence[str] | None = "f6_03_intervention_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column(
            "enrollment_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_sessions_enrollment_id",
        "sessions",
        "participant_enrollments",
        ["enrollment_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_sessions_enrollment_id",
        "sessions",
        ["enrollment_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_sessions_enrollment_id", table_name="sessions")
    op.drop_constraint("fk_sessions_enrollment_id", "sessions", type_="foreignkey")
    op.drop_column("sessions", "enrollment_id")
