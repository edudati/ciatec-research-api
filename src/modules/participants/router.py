"""Participant profile HTTP routes (ADMIN or PI)."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.openapi_schemas import ApiErrorResponse
from src.modules.auth.deps import require_admin_or_pi
from src.modules.participants.schemas import (
    ParticipantCreateIn,
    ParticipantListResponse,
    ParticipantOut,
    ParticipantUpdateIn,
)
from src.modules.participants.service import ParticipantsService


def get_participants_service(
    db: AsyncSession = Depends(get_db),
) -> ParticipantsService:
    return ParticipantsService(db)


router = APIRouter(
    prefix="/api/v1/participants",
    tags=["Participants"],
    dependencies=[Depends(require_admin_or_pi)],
)

SortField = Literal["createdAt", "updatedAt"]
OrderDir = Literal["asc", "desc"]


@router.get(
    "",
    response_model=ParticipantListResponse,
    response_model_by_alias=True,
    summary="List participant profiles",
    description="Paginated list of participant profiles (not soft-deleted).",
)
async def list_participants(
    service: ParticipantsService = Depends(get_participants_service),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
    q: str | None = Query(
        None,
        description="Case-insensitive match on user name, email, or notes",
    ),
    sort: SortField = Query(
        "createdAt",
        description="Sort field: createdAt, updatedAt",
    ),
    order: OrderDir = Query("desc", description="Sort direction: asc or desc"),
) -> ParticipantListResponse:
    return await service.list_participants(
        page=page,
        page_size=page_size,
        q=q,
        sort=sort,
        order=order,
    )


@router.post(
    "",
    response_model=ParticipantOut,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    summary="Create participant profile",
    description="Creates a longitudinal profile for an existing active user.",
    responses={
        409: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
    },
)
async def create_participant(
    body: ParticipantCreateIn,
    service: ParticipantsService = Depends(get_participants_service),
) -> ParticipantOut:
    return await service.create(body)


@router.get(
    "/{participant_id}",
    response_model=ParticipantOut,
    response_model_by_alias=True,
    summary="Get participant profile by id",
    responses={403: {"model": ApiErrorResponse}},
)
async def get_participant(
    participant_id: UUID,
    service: ParticipantsService = Depends(get_participants_service),
) -> ParticipantOut:
    return await service.get_by_id(participant_id)


@router.patch(
    "/{participant_id}",
    response_model=ParticipantOut,
    response_model_by_alias=True,
    summary="Update participant profile",
    responses={403: {"model": ApiErrorResponse}},
)
async def update_participant(
    participant_id: UUID,
    body: ParticipantUpdateIn,
    service: ParticipantsService = Depends(get_participants_service),
) -> ParticipantOut:
    return await service.update(participant_id, body)
