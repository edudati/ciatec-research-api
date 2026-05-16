"""FastAPI dependencies for project assessment records."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.project_assessments.service import AssessmentRecordsService


def get_assessment_records_service(
    db: AsyncSession = Depends(get_db),
) -> AssessmentRecordsService:
    return AssessmentRecordsService(db)
