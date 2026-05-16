"""HTTP routes for project timeline export (F10-02)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from src.core.openapi_schemas import ApiErrorResponse
from src.models.user import User
from src.modules.auth.deps import require_active_user
from src.modules.project_exports.deps import get_project_exports_service
from src.modules.project_exports.schemas import (
    ProjectExportJobStatusOut,
    ProjectExportQueuedOut,
)
from src.modules.project_exports.service import ProjectExportsService

router = APIRouter(prefix="/api/v1/projects", tags=["Project exports"])


@router.get(
    "/{project_id}/export/jobs/{job_id}/download",
    summary="Download completed async export file",
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse},
    },
)
async def download_project_export(
    project_id: UUID,
    job_id: UUID,
    viewer: User = Depends(require_active_user),
    service: ProjectExportsService = Depends(get_project_exports_service),
) -> FileResponse:
    path, fmt = await service.read_download_path(project_id, job_id, viewer)
    if fmt == "csv":
        media = "text/csv; charset=utf-8"
    else:
        media = "application/json; charset=utf-8"
    suffix = "csv" if fmt == "csv" else "json"
    return FileResponse(
        path,
        media_type=media,
        filename=f"project-{project_id}-timeline.{suffix}",
    )


@router.get(
    "/{project_id}/export/jobs/{job_id}",
    response_model=ProjectExportJobStatusOut,
    response_model_by_alias=True,
    summary="Poll async export job status",
    responses={
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
    },
)
async def get_project_export_job(
    project_id: UUID,
    job_id: UUID,
    viewer: User = Depends(require_active_user),
    service: ProjectExportsService = Depends(get_project_exports_service),
) -> ProjectExportJobStatusOut:
    return await service.get_job_status(project_id, job_id, viewer)


@router.get(
    "/{project_id}/export",
    response_model=None,
    summary=(
        "Export project timeline (CSV or JSON bundle_v1). "
        "Use async=true or rely on row threshold for 202 + job polling. "
        "Poll GET .../export/jobs/{jobId} until ready=true, then download."
    ),
    responses={
        202: {"model": ProjectExportQueuedOut},
        401: {"model": ApiErrorResponse},
        403: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        422: {"model": ApiErrorResponse},
    },
)
async def export_project_timeline(
    project_id: UUID,
    format: str = Query(
        "csv",
        description="Export format: csv or json (case-insensitive)",
    ),
    run_async: bool = Query(
        False,
        alias="async",
        description="Force asynchronous export (returns job id; requires Redis + arq)",
    ),
    viewer: User = Depends(require_active_user),
    service: ProjectExportsService = Depends(get_project_exports_service),
) -> StreamingResponse | JSONResponse:
    export_fmt = service.validate_export_format(format)
    use_async = await service.should_use_async(project_id, run_async=run_async)
    if use_async:
        out = await service.enqueue_export(
            project_id,
            export_format=export_fmt,
            actor=viewer,
        )
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=out.model_dump(mode="json", by_alias=True),
        )
    if export_fmt == "csv":
        return StreamingResponse(
            service.stream_csv(project_id, viewer),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="project-{project_id}-timeline.csv"'
                ),
            },
        )
    return StreamingResponse(
        service.stream_json(project_id, viewer),
        media_type="application/json; charset=utf-8",
        headers={
            "Content-Disposition": (
                f'attachment; filename="project-{project_id}-timeline.json"'
            ),
        },
    )
