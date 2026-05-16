"""F3-03: one project member role per user per project.

Revision ID: f3_03_project_members_user
Revises: f3_02_groups
"""

from collections.abc import Sequence

from alembic import op

revision: str = "f3_03_project_members_user"
down_revision: str | Sequence[str] | None = "f3_02_groups"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_project_members_project_user_role",
        "project_members",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_project_members_project_user",
        "project_members",
        ["project_id", "user_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_project_members_project_user",
        "project_members",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_project_members_project_user_role",
        "project_members",
        ["project_id", "user_id", "role"],
    )
