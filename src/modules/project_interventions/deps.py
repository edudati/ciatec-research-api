"""FastAPI dependencies for project intervention records."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.project_interventions.service import InterventionRecordsService


def get_intervention_records_service(
    db: AsyncSession = Depends(get_db),
) -> InterventionRecordsService:
    return InterventionRecordsService(db)
