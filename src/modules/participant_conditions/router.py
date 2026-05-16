"""HTTP routes for participant x health condition temporal links."""

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from src.core.openapi_schemas import ApiErrorResponse
from src.modules.auth.deps import require_admin_or_pi
from src.modules.participant_conditions.deps import get_participant_conditions_service
from src.modules.participant_conditions.schemas import (
    ParticipantConditionCreateIn,
    ParticipantConditionListResponse,
    ParticipantConditionOut,
    ParticipantConditionPatchIn,
)
from src.modules.participant_conditions.service import ParticipantConditionsService

router = APIRouter(
    prefix="/api/v1/participants/{participant_id}/conditions",
    tags=["Participant conditions"],
    dependencies=[Depends(require_admin_or_pi)],
)


@router.get(
    "",
    response_model=ParticipantConditionListResponse,
    response_model_by_alias=True,
    summary="List participant condition links",
    description="Temporal links between a participant profile and health conditions.",
    responses={403: {"model": ApiErrorResponse}, 404: {"model": ApiErrorResponse}},
)
async def list_participant_conditions(
    participant_id: UUID,
    service: ParticipantConditionsService = Depends(get_participant_conditions_service),
) -> ParticipantConditionListResponse:
    return await service.list_for_participant(participant_id)


@router.post(
    "",
    response_model=ParticipantConditionOut,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=True,
    summary="Link a health condition to a participant",
    responses={
        400: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def create_participant_condition(
    participant_id: UUID,
    body: ParticipantConditionCreateIn,
    service: ParticipantConditionsService = Depends(get_participant_conditions_service),
) -> ParticipantConditionOut:
    return await service.create(participant_id, body)


@router.patch(
    "/{condition_id}",
    response_model=ParticipantConditionOut,
    response_model_by_alias=True,
    summary="Update a participant condition link",
    responses={
        400: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def patch_participant_condition(
    participant_id: UUID,
    condition_id: UUID,
    body: ParticipantConditionPatchIn,
    service: ParticipantConditionsService = Depends(get_participant_conditions_service),
) -> ParticipantConditionOut:
    return await service.patch(participant_id, condition_id, body)


@router.delete(
    "/{condition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a participant condition link",
    responses={
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def delete_participant_condition(
    participant_id: UUID,
    condition_id: UUID,
    service: ParticipantConditionsService = Depends(get_participant_conditions_service),
) -> Response:
    await service.delete(participant_id, condition_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
