"""Intervention template HTTP routes under /api/v1/instruments/interventions."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.openapi_schemas import ApiErrorResponse
from src.modules.auth.deps import require_admin
from src.modules.instruments.deps import get_intervention_templates_service
from src.modules.instruments.schemas_interventions import (
    InterventionTemplateCreateIn,
    InterventionTemplateOut,
    InterventionTemplatesListResponse,
    InterventionTemplateUpdateIn,
)
from src.modules.instruments.service_interventions import InterventionTemplatesService

interventions_router = APIRouter(prefix="/interventions", tags=["Instruments"])

SortField = Literal["createdAt", "name", "code", "updatedAt"]
OrderDir = Literal["asc", "desc"]


@interventions_router.get(
    "",
    response_model=InterventionTemplatesListResponse,
    response_model_by_alias=True,
    summary="List intervention templates",
    description="Public paginated list of intervention templates.",
)
async def list_intervention_templates(
    service: InterventionTemplatesService = Depends(get_intervention_templates_service),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
    sort: SortField = Query(
        "createdAt",
        description="Sort field: createdAt, name, code, updatedAt",
    ),
    order: OrderDir = Query("desc", description="Sort direction: asc or desc"),
) -> InterventionTemplatesListResponse:
    return await service.list_public(
        page=page,
        page_size=page_size,
        sort=sort,
        order=order,
    )


@interventions_router.get(
    "/{template_id}",
    response_model=InterventionTemplateOut,
    response_model_by_alias=True,
    summary="Get intervention template by id",
    responses={404: {"model": ApiErrorResponse}},
)
async def get_intervention_template(
    template_id: UUID,
    service: InterventionTemplatesService = Depends(get_intervention_templates_service),
) -> InterventionTemplateOut:
    return await service.get_by_id(template_id)


@interventions_router.post(
    "",
    response_model=InterventionTemplateOut,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    summary="Create intervention template",
    dependencies=[Depends(require_admin)],
    responses={
        400: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
async def create_intervention_template(
    body: InterventionTemplateCreateIn,
    service: InterventionTemplatesService = Depends(get_intervention_templates_service),
) -> InterventionTemplateOut:
    return await service.create(body)


@interventions_router.patch(
    "/{template_id}",
    response_model=InterventionTemplateOut,
    response_model_by_alias=True,
    summary="Update intervention template",
    dependencies=[Depends(require_admin)],
    responses={
        400: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
async def patch_intervention_template(
    template_id: UUID,
    body: InterventionTemplateUpdateIn,
    service: InterventionTemplatesService = Depends(get_intervention_templates_service),
) -> InterventionTemplateOut:
    return await service.update(template_id, body)
