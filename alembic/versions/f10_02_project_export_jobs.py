"""F10-02: project_export_jobs for async scientific exports.

Revision ID: f10_02_project_export_jobs
Revises: f9_01_self_report_tokens
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f10_02_project_export_jobs"
down_revision: str | Sequence[str] | None = "f9_01_self_report_tokens"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "project_export_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "requested_by_user_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("format", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("result_path", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_project_export_jobs_project_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_user_id"],
            ["users.id"],
            name="fk_project_export_jobs_requested_by_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_project_export_jobs_project_id",
        "project_export_jobs",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_export_jobs_requested_by_user_id",
        "project_export_jobs",
        ["requested_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_project_export_jobs_requested_by_user_id",
        table_name="project_export_jobs",
    )
    op.drop_index(
        "ix_project_export_jobs_project_id",
        table_name="project_export_jobs",
    )
    op.drop_table("project_export_jobs")
