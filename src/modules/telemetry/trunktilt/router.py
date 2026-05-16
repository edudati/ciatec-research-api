"""TrunkTilt typed telemetry routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.core.openapi_schemas import ApiErrorResponse
from src.modules.auth.deps import get_access_user_id
from src.modules.telemetry.trunktilt.deps import get_trunktilt_telemetry_service
from src.modules.telemetry.trunktilt.schemas import (
    EventsBatchIn,
    EventsBatchOut,
    PoseBatchIn,
    PoseBatchOut,
    WorldBatchIn,
    WorldBatchOut,
)
from src.modules.telemetry.trunktilt.service import TrunkTiltTelemetryService

router = APIRouter(
    prefix="/api/v1/trunktilt/matches",
    tags=["TrunkTilt"],
    dependencies=[Depends(get_access_user_id)],
)


_TELEMETRY_RESPONSES: dict[int | str, dict[str, object]] = {
    400: {"description": "Validation error"},
    401: {"description": "Unauthorized"},
    403: {"description": "Not a TrunkTilt match"},
    404: {"description": "Match not found"},
    409: {"description": "Match already finished", "model": ApiErrorResponse},
}


@router.post(
    "/{match_id}/telemetry/world",
    response_model=WorldBatchOut,
    status_code=status.HTTP_202_ACCEPTED,
    summary="TrunkTilt world telemetry batch",
    description=(
        "Stores typed world-state samples for a TrunkTilt match (ball, plane tilt, "
        "virtual input). Match must belong to TrunkTilt and not be finished. "
        "Idempotent per (match_id, frame_id)."
    ),
    responses=_TELEMETRY_RESPONSES,
)
async def post_trunktilt_world(
    match_id: UUID,
    body: WorldBatchIn,
    user_id: UUID = Depends(get_access_user_id),
    service: TrunkTiltTelemetryService = Depends(get_trunktilt_telemetry_service),
) -> WorldBatchOut:
    return await service.ingest_world(user_id, match_id, body)


@router.post(
    "/{match_id}/telemetry/pose",
    response_model=PoseBatchOut,
    status_code=status.HTTP_202_ACCEPTED,
    summary="TrunkTilt pose landmarks batch",
    description=(
        "Stores MediaPipe Pose landmarks per frame (33 landmark ids 0–32). "
        "Idempotent per (match_id, frame_id, landmark_id)."
    ),
    responses=_TELEMETRY_RESPONSES,
)
async def post_trunktilt_pose(
    match_id: UUID,
    body: PoseBatchIn,
    user_id: UUID = Depends(get_access_user_id),
    service: TrunkTiltTelemetryService = Depends(get_trunktilt_telemetry_service),
) -> PoseBatchOut:
    return await service.ingest_pose(user_id, match_id, body)


@router.post(
    "/{match_id}/events",
    response_model=EventsBatchOut,
    status_code=status.HTTP_201_CREATED,
    summary="TrunkTilt discrete events batch",
    description=(
        "Stores gameplay events for a TrunkTilt match. "
        "Match must be TrunkTilt and not finished."
    ),
    responses=_TELEMETRY_RESPONSES,
)
async def post_trunktilt_events(
    match_id: UUID,
    body: EventsBatchIn,
    user_id: UUID = Depends(get_access_user_id),
    service: TrunkTiltTelemetryService = Depends(get_trunktilt_telemetry_service),
) -> EventsBatchOut:
    return await service.ingest_events(user_id, match_id, body)
