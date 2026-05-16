"""FastAPI dependencies for project questionnaire responses."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.project_questionnaires.service import QuestionnaireResponsesService


def get_questionnaire_responses_service(
    db: AsyncSession = Depends(get_db),
) -> QuestionnaireResponsesService:
    return QuestionnaireResponsesService(db)
