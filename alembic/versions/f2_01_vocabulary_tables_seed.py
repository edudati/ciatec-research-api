"""F2-01: vocabulary_schemes, vocabulary_terms, and CRIS seed.

Revision ID: f2_01_vocab
Revises: f1_03_participant_cond_temp
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f2_01_vocab"
down_revision: str | Sequence[str] | None = "f1_03_participant_cond_temp"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uid(key: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"ciatec-research-api.vocab:{key}"))


_SCHEME_ROWS: list[tuple[str, str, str | None]] = [
    ("PROJECT_MEMBER_ROLE", "Project member role", None),
    ("ENROLLMENT_ROLE", "Enrollment role", None),
    ("ENROLLMENT_STATUS", "Enrollment status", None),
    ("TIMELINE_EVENT_TYPE", "Timeline event type", None),
    ("CONDITION_SEVERITY", "Condition severity", None),
    ("BIOLOGICAL_SEX", "Biological sex", None),
    ("ASSESSMENT_TYPE", "Assessment type", None),
    ("INTERVENTION_TYPE", "Intervention type", None),
    ("INSTRUMENT_INDICATION_TYPE", "Instrument indication type", None),
]

_TERM_DEFS: dict[str, list[tuple[str, str]]] = {
    "PROJECT_MEMBER_ROLE": [
        ("PI", "PI"),
        ("RESEARCHER", "Researcher"),
        ("ASSISTANT", "Assistant"),
        ("COLLABORATOR", "Collaborator"),
    ],
    "ENROLLMENT_ROLE": [
        ("PARTICIPANT", "Participant"),
        ("CONTROL", "Control"),
        ("PILOT", "Pilot"),
    ],
    "ENROLLMENT_STATUS": [
        ("ACTIVE", "Active"),
        ("COMPLETED", "Completed"),
        ("WITHDRAWN", "Withdrawn"),
        ("SCREENING", "Screening"),
    ],
    "TIMELINE_EVENT_TYPE": [
        ("ASSESSMENT", "Assessment"),
        ("QUESTIONNAIRE", "Questionnaire"),
        ("INTERVENTION", "Intervention"),
        ("GAME_SESSION", "Game session"),
        ("ENROLLMENT", "Enrollment"),
        ("CONDITION_CHANGE", "Condition change"),
        ("NOTE", "Note"),
    ],
    "CONDITION_SEVERITY": [
        ("MILD", "Mild"),
        ("MODERATE", "Moderate"),
        ("SEVERE", "Severe"),
    ],
    "BIOLOGICAL_SEX": [
        ("M", "M"),
        ("F", "F"),
        ("OTHER", "Other"),
    ],
    "ASSESSMENT_TYPE": [
        ("FUNCTIONAL", "Functional"),
        ("COGNITIVE", "Cognitive"),
        ("MOTOR", "Motor"),
        ("PSYCHOLOGICAL", "Psychological"),
    ],
    "INTERVENTION_TYPE": [
        ("GAME", "Game"),
        ("EXERCISE", "Exercise"),
        ("INTERVIEW", "Interview"),
        ("CLINICAL_EXAM", "Clinical exam"),
        ("CONSULTATION", "Consultation"),
    ],
    "INSTRUMENT_INDICATION_TYPE": [
        ("INDICATED", "Indicated"),
        ("COMMONLY_USED", "Commonly used"),
        ("GOLD_STANDARD", "Gold standard"),
    ],
}


def upgrade() -> None:
    op.create_table(
        "vocabulary_schemes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_vocabulary_schemes_code"),
    )

    op.create_table(
        "vocabulary_terms",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "scheme_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "sort_order",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["scheme_id"],
            ["vocabulary_schemes.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "scheme_id",
            "code",
            name="uq_vocabulary_terms_scheme_code",
        ),
    )
    op.create_index(
        "ix_vocabulary_terms_scheme_id",
        "vocabulary_terms",
        ["scheme_id"],
        unique=False,
    )

    scheme_table = sa.table(
        "vocabulary_schemes",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
    )
    term_table = sa.table(
        "vocabulary_terms",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("scheme_id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("label", sa.String),
        sa.column("description", sa.Text),
        sa.column("is_active", sa.Boolean),
        sa.column("sort_order", sa.Integer),
    )

    scheme_rows: list[dict[str, object]] = []
    for code, name, desc in _SCHEME_ROWS:
        scheme_rows.append(
            {
                "id": uuid.UUID(_uid(f"scheme:{code}")),
                "code": code,
                "name": name,
                "description": desc,
            },
        )
    op.bulk_insert(scheme_table, scheme_rows)

    term_rows: list[dict[str, object]] = []
    for scheme_code, pairs in _TERM_DEFS.items():
        sid = uuid.UUID(_uid(f"scheme:{scheme_code}"))
        for order, (tcode, label) in enumerate(pairs):
            term_rows.append(
                {
                    "id": uuid.UUID(_uid(f"term:{scheme_code}:{tcode}")),
                    "scheme_id": sid,
                    "code": tcode,
                    "label": label,
                    "description": None,
                    "is_active": True,
                    "sort_order": order,
                },
            )
    op.bulk_insert(term_table, term_rows)


def downgrade() -> None:
    op.drop_index("ix_vocabulary_terms_scheme_id", table_name="vocabulary_terms")
    op.drop_table("vocabulary_terms")
    op.drop_table("vocabulary_schemes")
