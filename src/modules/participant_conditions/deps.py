"""Dependency providers for participant condition links."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.participant_conditions.service import ParticipantConditionsService


def get_participant_conditions_service(
    db: AsyncSession = Depends(get_db),
) -> ParticipantConditionsService:
    return ParticipantConditionsService(db)
