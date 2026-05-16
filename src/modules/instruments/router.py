"""Assessment template HTTP routes under /api/v1/instruments."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.openapi_schemas import ApiErrorResponse
from src.modules.auth.deps import require_admin
from src.modules.instruments.deps import get_assessment_templates_service
from src.modules.instruments.router_indications import indications_router
from src.modules.instruments.router_interventions import interventions_router
from src.modules.instruments.router_questionnaires import questionnaires_router
from src.modules.instruments.schemas import (
    AssessmentTemplateCreateIn,
    AssessmentTemplateOut,
    AssessmentTemplatesListResponse,
    AssessmentTemplateUpdateIn,
)
from src.modules.instruments.service import AssessmentTemplatesService

router = APIRouter(prefix="/api/v1/instruments", tags=["Instruments"])
router.include_router(questionnaires_router)
router.include_router(interventions_router)
router.include_router(indications_router)

SortField = Literal["createdAt", "name", "code", "updatedAt"]
OrderDir = Literal["asc", "desc"]


@router.get(
    "/assessments",
    response_model=AssessmentTemplatesListResponse,
    response_model_by_alias=True,
    summary="List assessment templates",
    description="Public list: active templates only.",
)
async def list_assessment_templates(
    service: AssessmentTemplatesService = Depends(get_assessment_templates_service),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
    sort: SortField = Query(
        "createdAt",
        description="Sort field: createdAt, name, code, updatedAt",
    ),
    order: OrderDir = Query("desc", description="Sort direction: asc or desc"),
) -> AssessmentTemplatesListResponse:
    return await service.list_public(
        page=page,
        page_size=page_size,
        sort=sort,
        order=order,
    )


@router.get(
    "/assessments/{template_id}",
    response_model=AssessmentTemplateOut,
    response_model_by_alias=True,
    summary="Get assessment template by id",
    description="Public: active templates only.",
    responses={404: {"model": ApiErrorResponse}},
)
async def get_assessment_template(
    template_id: UUID,
    service: AssessmentTemplatesService = Depends(get_assessment_templates_service),
) -> AssessmentTemplateOut:
    return await service.get_public(template_id)


@router.post(
    "/assessments",
    response_model=AssessmentTemplateOut,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    summary="Create assessment template",
    dependencies=[Depends(require_admin)],
    responses={
        400: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
async def create_assessment_template(
    body: AssessmentTemplateCreateIn,
    service: AssessmentTemplatesService = Depends(get_assessment_templates_service),
) -> AssessmentTemplateOut:
    return await service.create(body)


@router.patch(
    "/assessments/{template_id}",
    response_model=AssessmentTemplateOut,
    response_model_by_alias=True,
    summary="Update assessment template",
    dependencies=[Depends(require_admin)],
    responses={
        400: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
async def patch_assessment_template(
    template_id: UUID,
    body: AssessmentTemplateUpdateIn,
    service: AssessmentTemplatesService = Depends(get_assessment_templates_service),
) -> AssessmentTemplateOut:
    return await service.update(template_id, body)
