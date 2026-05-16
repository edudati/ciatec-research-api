"""Participant x health condition temporal link (CERIF-style)."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.health_condition import HealthCondition
    from src.models.participant_profile import ParticipantProfile


class ParticipantCondition(Base):
    __tablename__ = "participant_conditions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    participant_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("participant_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    health_condition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("health_conditions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    diagnosed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    resolved_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    severity: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    participant_profile: Mapped["ParticipantProfile"] = relationship(
        "ParticipantProfile",
        back_populates="condition_links",
        lazy="raise",
    )
    health_condition: Mapped["HealthCondition"] = relationship(
        "HealthCondition",
        back_populates="participant_links",
        lazy="raise",
    )
