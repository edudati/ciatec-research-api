"""Initial empty migration (F0-01).

Revision ID: f0_01_initial
Revises:
Create Date: 2026-05-13

"""

from collections.abc import Sequence

revision: str = "f0_01_initial"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
