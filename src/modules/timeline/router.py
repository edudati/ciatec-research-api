"""HTTP routes for longitudinal timeline (read-only)."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.core.openapi_schemas import ApiErrorResponse
from src.models.user import User
from src.modules.auth.deps import require_active_user, require_admin_or_pi
from src.modules.timeline.deps import get_timeline_service
from src.modules.timeline.schemas import TimelineListResponse
from src.modules.timeline.service import TimelineService

router = APIRouter(prefix="/api/v1", tags=["Timeline"])


def _list_query_params(
    event_type: str | None = Query(
        None,
        alias="eventType",
        description="Filter by timeline event type code (e.g. ASSESSMENT, ENROLLMENT)",
    ),
    from_date: date | None = Query(
        None,
        alias="fromDate",
        description="Inclusive lower bound on occurredAt (date, UTC day start)",
    ),
    to_date: date | None = Query(
        None,
        alias="toDate",
        description="Inclusive upper bound on occurredAt (date, UTC day end)",
    ),
    executor_id: UUID | None = Query(
        None,
        alias="executorId",
        description="Filter events by executor user id",
    ),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
) -> tuple[str | None, date | None, date | None, UUID | None, int, int]:
    return (event_type, from_date, to_date, executor_id, page, page_size)


@router.get(
    "/participants/{participant_id}/timeline",
    response_model=TimelineListResponse,
    response_model_by_alias=True,
    summary="Participant timeline (personal scope)",
    description=(
        "All timeline events for a participant profile across projects. "
        "ADMIN or PI only. Ordered by occurredAt descending."
    ),
    responses={
        400: {"model": ApiErrorResponse},
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def list_participant_timeline(
    participant_id: UUID,
    viewer: User = Depends(require_admin_or_pi),
    service: TimelineService = Depends(get_timeline_service),
    qp: tuple[str | None, date | None, date | None, UUID | None, int, int] = Depends(
        _list_query_params,
    ),
) -> TimelineListResponse:
    event_type, from_date, to_date, executor_id, page, page_size = qp
    return await service.list_for_participant(
        participant_id,
        _viewer=viewer,
        event_type=event_type,
        from_date=from_date,
        to_date=to_date,
        executor_id=executor_id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/projects/{project_id}/timeline",
    response_model=TimelineListResponse,
    response_model_by_alias=True,
    summary="Project timeline",
    description=(
        "Timeline events for one project. Project members may access; "
        "RESEARCHER only sees events where they are the executor (executorId matches "
        "their user). Events with no executor (e.g. some automated flows) are hidden "
        "from RESEARCHER in this view. Ordered by occurredAt descending."
    ),
    responses={
        400: {"model": ApiErrorResponse},
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def list_project_timeline(
    project_id: UUID,
    viewer: User = Depends(require_active_user),
    service: TimelineService = Depends(get_timeline_service),
    qp: tuple[str | None, date | None, date | None, UUID | None, int, int] = Depends(
        _list_query_params,
    ),
) -> TimelineListResponse:
    event_type, from_date, to_date, executor_id, page, page_size = qp
    return await service.list_for_project(
        project_id,
        viewer=viewer,
        event_type=event_type,
        from_date=from_date,
        to_date=to_date,
        executor_id=executor_id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/timeline",
    response_model=TimelineListResponse,
    response_model_by_alias=True,
    summary="Global timeline",
    description=(
        "Unscoped timeline across all projects and participants. "
        "ADMIN or PI only. Ordered by occurredAt descending."
    ),
    responses={
        400: {"model": ApiErrorResponse},
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
    },
)
async def list_global_timeline(
    viewer: User = Depends(require_admin_or_pi),
    service: TimelineService = Depends(get_timeline_service),
    qp: tuple[str | None, date | None, date | None, UUID | None, int, int] = Depends(
        _list_query_params,
    ),
) -> TimelineListResponse:
    event_type, from_date, to_date, executor_id, page, page_size = qp
    return await service.list_global(
        _viewer=viewer,
        event_type=event_type,
        from_date=from_date,
        to_date=to_date,
        executor_id=executor_id,
        page=page,
        page_size=page_size,
    )
