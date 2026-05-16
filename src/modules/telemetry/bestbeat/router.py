"""Bestbeat JSON telemetry routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.core.openapi_schemas import ApiErrorResponse
from src.modules.auth.deps import get_access_user_id
from src.modules.telemetry.bestbeat.deps import get_bestbeat_telemetry_service
from src.modules.telemetry.bestbeat.schemas import (
    EventsBatchIn,
    EventsBatchOut,
    PoseBatchIn,
    PoseBatchOut,
    WorldBatchIn,
    WorldBatchOut,
)
from src.modules.telemetry.bestbeat.service import BestbeatTelemetryService

router = APIRouter(
    prefix="/api/v1/bestbeat/matches",
    tags=["Bestbeat"],
    dependencies=[Depends(get_access_user_id)],
)


@router.post(
    "/{match_id}/telemetry/world",
    response_model=WorldBatchOut,
    status_code=status.HTTP_201_CREATED,
    summary="Bestbeat world telemetry batch",
    description=(
        "Stores world / device-attributed telemetry frames (JSON `data`). "
        "Match must belong to Bestbeat and not be finished. "
        "Idempotent per (match_id, timestamp_ms, device)."
    ),
    responses={
        400: {"description": "Validation error"},
        401: {"description": "Unauthorized"},
        403: {"description": "Not a Bestbeat match"},
        404: {"description": "Match not found"},
        409: {"description": "Match already finished", "model": ApiErrorResponse},
    },
)
async def post_bestbeat_world(
    match_id: UUID,
    body: WorldBatchIn,
    user_id: UUID = Depends(get_access_user_id),
    service: BestbeatTelemetryService = Depends(get_bestbeat_telemetry_service),
) -> WorldBatchOut:
    return await service.ingest_world(user_id, match_id, body)


@router.post(
    "/{match_id}/telemetry/pose",
    response_model=PoseBatchOut,
    status_code=status.HTTP_201_CREATED,
    summary="Bestbeat pose telemetry batch",
    description=(
        "Stores per-frame pose-style samples in JSON `data`. "
        "Match must be Bestbeat and not finished. "
        "Idempotent per (match_id, timestamp_ms)."
    ),
    responses={
        400: {"description": "Validation error"},
        401: {"description": "Unauthorized"},
        403: {"description": "Not a Bestbeat match"},
        404: {"description": "Match not found"},
        409: {"description": "Match already finished", "model": ApiErrorResponse},
    },
)
async def post_bestbeat_pose(
    match_id: UUID,
    body: PoseBatchIn,
    user_id: UUID = Depends(get_access_user_id),
    service: BestbeatTelemetryService = Depends(get_bestbeat_telemetry_service),
) -> PoseBatchOut:
    return await service.ingest_pose(user_id, match_id, body)


@router.post(
    "/{match_id}/events",
    response_model=EventsBatchOut,
    status_code=status.HTTP_201_CREATED,
    summary="Bestbeat discrete events batch",
    description=(
        "Stores gameplay events for a Bestbeat match (`type`, `timestamp`, `data`). "
        "Match must be Bestbeat and not be finished."
    ),
    responses={
        400: {"description": "Validation error"},
        401: {"description": "Unauthorized"},
        403: {"description": "Not a Bestbeat match"},
        404: {"description": "Match not found"},
        409: {"description": "Match already finished", "model": ApiErrorResponse},
    },
)
async def post_bestbeat_events(
    match_id: UUID,
    body: EventsBatchIn,
    user_id: UUID = Depends(get_access_user_id),
    service: BestbeatTelemetryService = Depends(get_bestbeat_telemetry_service),
) -> EventsBatchOut:
    return await service.ingest_events(user_id, match_id, body)
