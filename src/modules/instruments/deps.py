"""FastAPI dependencies for instruments domain."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.instruments.service import AssessmentTemplatesService
from src.modules.instruments.service_indications import InstrumentIndicationsService
from src.modules.instruments.service_interventions import InterventionTemplatesService
from src.modules.instruments.service_questionnaires import QuestionnairesService


def get_assessment_templates_service(
    db: AsyncSession = Depends(get_db),
) -> AssessmentTemplatesService:
    return AssessmentTemplatesService(db)


def get_instrument_indications_service(
    db: AsyncSession = Depends(get_db),
) -> InstrumentIndicationsService:
    return InstrumentIndicationsService(db)


def get_intervention_templates_service(
    db: AsyncSession = Depends(get_db),
) -> InterventionTemplatesService:
    return InterventionTemplatesService(db)


def get_questionnaires_service(
    db: AsyncSession = Depends(get_db),
) -> QuestionnairesService:
    return QuestionnairesService(db)
