"""F5-04: instrument_indications (clinical instrument links to conditions).

Revision ID: f5_04_instrument_indications
Revises: f5_03_intervention_templates
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f5_04_instrument_indications"
down_revision: str | Sequence[str] | None = "f5_03_intervention_templates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "instrument_indications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instrument_type", sa.String(length=32), nullable=False),
        sa.Column("instrument_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("health_condition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("indication_type", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "instrument_type IN ('ASSESSMENT', 'QUESTIONNAIRE')",
            name="ck_instrument_indications_instrument_type",
        ),
        sa.ForeignKeyConstraint(
            ["health_condition_id"],
            ["health_conditions.id"],
            name="fk_instrument_indications_health_condition_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "instrument_type",
            "instrument_id",
            "health_condition_id",
            name="uq_instrument_indications_triple",
        ),
    )
    op.create_index(
        "ix_instrument_indications_health_condition_id",
        "instrument_indications",
        ["health_condition_id"],
        unique=False,
    )
    op.create_index(
        "ix_instrument_indications_instrument",
        "instrument_indications",
        ["instrument_type", "instrument_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_instrument_indications_instrument",
        table_name="instrument_indications",
    )
    op.drop_index(
        "ix_instrument_indications_health_condition_id",
        table_name="instrument_indications",
    )
    op.drop_table("instrument_indications")
