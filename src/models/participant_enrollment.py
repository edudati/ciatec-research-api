"""Participant enrollment (CRIS CERIF link)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.participant_profile import ParticipantProfile
from src.models.project import Project, ProjectGroup
from src.models.user import User


class ParticipantEnrollment(Base):
    __tablename__ = "participant_enrollments"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "participant_profile_id",
            name="uq_participant_enrollments_project_profile",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    participant_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("participant_profiles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    group_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    exited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    exit_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    enrolled_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    project: Mapped[Project] = relationship(
        "Project",
        lazy="raise",
        foreign_keys=[project_id],
    )
    participant_profile: Mapped[ParticipantProfile] = relationship(
        "ParticipantProfile",
        lazy="raise",
        foreign_keys=[participant_profile_id],
    )
    group: Mapped[ProjectGroup | None] = relationship(
        "ProjectGroup",
        back_populates="enrollments",
        lazy="raise",
        foreign_keys=[group_id],
    )
    enrolled_by_user: Mapped[User | None] = relationship(
        "User",
        lazy="raise",
        foreign_keys=[enrolled_by],
    )
