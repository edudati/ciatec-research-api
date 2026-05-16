"""Structured items belonging to a questionnaire template."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.questionnaire_template import QuestionnaireTemplate


class QuestionItem(Base):
    __tablename__ = "question_items"
    __table_args__ = (
        UniqueConstraint(
            "questionnaire_template_id",
            "code",
            name="uq_question_items_template_code",
        ),
        UniqueConstraint(
            "questionnaire_template_id",
            "order",
            name="uq_question_items_template_order",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    questionnaire_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questionnaire_templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(512), nullable=False)
    item_type: Mapped[str] = mapped_column("type", String(64), nullable=False)
    display_order: Mapped[int] = mapped_column("order", Integer, nullable=False)
    item_options: Mapped[dict[str, Any] | None] = mapped_column(
        "options",
        JSONB,
        nullable=True,
    )
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    template: Mapped["QuestionnaireTemplate"] = relationship(
        "QuestionnaireTemplate",
        back_populates="items",
        lazy="raise",
    )
