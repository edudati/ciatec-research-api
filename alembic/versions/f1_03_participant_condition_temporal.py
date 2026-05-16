"""F1-03: temporal fields and notes on participant_conditions.

Revision ID: f1_03_participant_cond_temp
Revises: f1_02_health_conditions

Adds diagnosed_at, resolved_at, severity (vocabulary code placeholder),
and notes. CHECK ensures resolved_at >= diagnosed_at when both set.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f1_03_participant_cond_temp"
down_revision: str | Sequence[str] | None = "f1_02_health_conditions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CHECK_NAME = "ck_participant_conditions_resolved_after_diagnosed"


def upgrade() -> None:
    op.add_column(
        "participant_conditions",
        sa.Column("diagnosed_at", sa.Date(), nullable=True),
    )
    op.add_column(
        "participant_conditions",
        sa.Column("resolved_at", sa.Date(), nullable=True),
    )
    op.add_column(
        "participant_conditions",
        sa.Column("severity", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "participant_conditions",
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_check_constraint(
        _CHECK_NAME,
        "participant_conditions",
        "diagnosed_at IS NULL OR resolved_at IS NULL OR resolved_at >= diagnosed_at",
    )


def downgrade() -> None:
    op.drop_constraint(_CHECK_NAME, "participant_conditions", type_="check")
    op.drop_column("participant_conditions", "notes")
    op.drop_column("participant_conditions", "severity")
    op.drop_column("participant_conditions", "resolved_at")
    op.drop_column("participant_conditions", "diagnosed_at")
