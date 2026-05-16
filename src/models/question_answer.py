"""Answer row for a questionnaire response instance."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.question_item import QuestionItem
    from src.models.questionnaire_response import QuestionnaireResponse


class QuestionAnswer(Base):
    __tablename__ = "question_answers"
    __table_args__ = (
        UniqueConstraint(
            "questionnaire_response_id",
            "question_item_id",
            name="uq_question_answers_response_item",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    questionnaire_response_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questionnaire_responses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_items.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    value: Mapped[Any] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    questionnaire_response: Mapped[QuestionnaireResponse] = relationship(
        "QuestionnaireResponse",
        back_populates="answers",
        lazy="raise",
    )
    question_item: Mapped[QuestionItem] = relationship(
        "QuestionItem",
        lazy="raise",
    )
