"""Health condition HTTP routes."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.openapi_schemas import ApiErrorResponse
from src.modules.auth.deps import require_admin
from src.modules.health_conditions.schemas import (
    HealthConditionCreateIn,
    HealthConditionListResponse,
    HealthConditionOut,
    HealthConditionUpdateIn,
)
from src.modules.health_conditions.service import HealthConditionsService


def get_health_conditions_service(
    db: AsyncSession = Depends(get_db),
) -> HealthConditionsService:
    return HealthConditionsService(db)


router = APIRouter(prefix="/api/v1/health-conditions", tags=["Health conditions"])

SortField = Literal["createdAt", "name", "code", "updatedAt"]
OrderDir = Literal["asc", "desc"]


@router.get(
    "",
    response_model=HealthConditionListResponse,
    response_model_by_alias=True,
    summary="List health conditions",
    description="Public list: only active, non-deleted rows. Optional category filter.",
)
async def list_health_conditions(
    service: HealthConditionsService = Depends(get_health_conditions_service),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
    category: str | None = Query(
        None,
        description="Exact category match (case-insensitive)",
    ),
    sort: SortField = Query(
        "createdAt",
        description="Sort field: createdAt, name, code, updatedAt",
    ),
    order: OrderDir = Query("desc", description="Sort direction: asc or desc"),
) -> HealthConditionListResponse:
    return await service.list_conditions(
        page=page,
        page_size=page_size,
        category=category,
        sort=sort,
        order=order,
        public_only=True,
    )


@router.get(
    "/{health_condition_id}",
    response_model=HealthConditionOut,
    response_model_by_alias=True,
    summary="Get health condition by id",
    description="Public: only active, non-deleted.",
)
async def get_health_condition(
    health_condition_id: UUID,
    service: HealthConditionsService = Depends(get_health_conditions_service),
) -> HealthConditionOut:
    return await service.get_public(health_condition_id)


@router.post(
    "",
    response_model=HealthConditionOut,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    summary="Create health condition",
    dependencies=[Depends(require_admin)],
    responses={
        409: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
    },
)
async def create_health_condition(
    body: HealthConditionCreateIn,
    service: HealthConditionsService = Depends(get_health_conditions_service),
) -> HealthConditionOut:
    return await service.create(body)


@router.patch(
    "/{health_condition_id}",
    response_model=HealthConditionOut,
    response_model_by_alias=True,
    summary="Update health condition",
    dependencies=[Depends(require_admin)],
    responses={
        409: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
    },
)
async def update_health_condition(
    health_condition_id: UUID,
    body: HealthConditionUpdateIn,
    service: HealthConditionsService = Depends(get_health_conditions_service),
) -> HealthConditionOut:
    return await service.update(health_condition_id, body)


@router.delete(
    "/{health_condition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete health condition",
    dependencies=[Depends(require_admin)],
    responses={
        409: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
    },
)
async def delete_health_condition(
    health_condition_id: UUID,
    service: HealthConditionsService = Depends(get_health_conditions_service),
) -> Response:
    await service.soft_delete(health_condition_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
