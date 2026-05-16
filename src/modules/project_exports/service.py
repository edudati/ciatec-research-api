"""Business logic for project timeline exports (F10-02)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.database import AsyncSessionLocal
from src.core.enums import UserRole
from src.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnprocessableEntityError,
)
from src.models.project_export_job import ProjectExportJob
from src.models.user import User
from src.modules.project_exports.constants import (
    EXPORT_FORMAT_CSV,
    EXPORT_FORMAT_JSON,
    JOB_STATUS_COMPLETED,
    JOB_STATUS_FAILED,
    JOB_STATUS_QUEUED,
    PROJECT_PI_ROLE_CODE,
)
from src.modules.project_exports.export_file import (
    count_timeline_rows,
    iter_csv_row_bytes,
    iter_json_bundle_bytes,
)
from src.modules.project_exports.repository import ProjectExportsRepository
from src.modules.project_exports.schemas import (
    ProjectExportJobStatusOut,
    ProjectExportQueuedOut,
)
from src.modules.projects.repository import ProjectsRepository
from src.modules.timeline.runtime import get_timeline_arq_pool


class ProjectExportsService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._projects = ProjectsRepository(session)
        self._exports = ProjectExportsRepository(session)
        self._settings = settings or get_settings()

    async def _assert_export_auth(self, project_id: uuid.UUID, user: User) -> None:
        if user.role == UserRole.ADMIN.value:
            return
        if await self._projects.user_is_pi_member(
            project_id,
            user.id,
            pi_role_code=PROJECT_PI_ROLE_CODE,
        ):
            return
        raise ForbiddenError(
            "Only admin or project PI can export this project",
            code="FORBIDDEN",
        )

    async def _get_project_or_404(self, project_id: uuid.UUID) -> None:
        row = await self._projects.get_project_public(project_id)
        if row is None:
            raise NotFoundError("Project not found", code="NOT_FOUND")

    def _normalize_format(self, raw: str) -> str:
        fmt = raw.strip().lower()
        if fmt not in (EXPORT_FORMAT_CSV, EXPORT_FORMAT_JSON):
            raise UnprocessableEntityError(
                "format must be csv or json",
                code="EXPORT_INVALID_FORMAT",
            )
        return fmt

    def validate_export_format(self, raw: str) -> str:
        return self._normalize_format(raw)

    async def enqueue_export(
        self,
        project_id: uuid.UUID,
        *,
        export_format: str,
        actor: User,
    ) -> ProjectExportQueuedOut:
        await self._get_project_or_404(project_id)
        await self._assert_export_auth(project_id, actor)
        fmt = self._normalize_format(export_format)
        pool = get_timeline_arq_pool()
        if pool is None:
            raise UnprocessableEntityError(
                "Async export requires Redis and a running arq worker",
                code="EXPORT_ASYNC_UNAVAILABLE",
            )
        job = ProjectExportJob(
            id=uuid.uuid4(),
            project_id=project_id,
            requested_by_user_id=actor.id,
            format=fmt,
            status=JOB_STATUS_QUEUED,
        )
        self._exports.add_job(job)
        await self._session.commit()
        try:
            from src.modules.project_exports import arq_tasks

            job_name = arq_tasks.generate_project_export.__qualname__
            await pool.enqueue_job(job_name, str(job.id))
        except Exception:
            async with AsyncSessionLocal() as session:
                failed = await session.get(ProjectExportJob, job.id)
                if failed is not None:
                    failed.status = JOB_STATUS_FAILED
                    failed.error_code = "ENQUEUE_FAILED"
                    failed.error_message = "Failed to enqueue export job"
                    await session.commit()
            raise UnprocessableEntityError(
                "Could not enqueue export job",
                code="EXPORT_ENQUEUE_FAILED",
            ) from None
        return ProjectExportQueuedOut(job_id=str(job.id), status="queued")

    async def get_job_status(
        self,
        project_id: uuid.UUID,
        job_id: uuid.UUID,
        viewer: User,
    ) -> ProjectExportJobStatusOut:
        await self._get_project_or_404(project_id)
        await self._assert_export_auth(project_id, viewer)
        job = await self._exports.get_job_for_project(project_id, job_id)
        if job is None:
            raise NotFoundError("Export job not found", code="NOT_FOUND")
        ready = job.status == JOB_STATUS_COMPLETED and bool(job.result_path)
        return ProjectExportJobStatusOut(
            job_id=str(job.id),
            status=job.status,
            ready=ready,
            row_count=job.row_count,
            error_code=job.error_code,
            error_message=job.error_message,
        )

    async def read_download_path(
        self,
        project_id: uuid.UUID,
        job_id: uuid.UUID,
        viewer: User,
    ) -> tuple[Path, str]:
        """Returns absolute file path and export format extension."""
        await self._get_project_or_404(project_id)
        await self._assert_export_auth(project_id, viewer)
        job = await self._exports.get_job_for_project(project_id, job_id)
        if job is None:
            raise NotFoundError("Export job not found", code="NOT_FOUND")
        if job.status != JOB_STATUS_COMPLETED:
            raise ConflictError(
                "Export is not ready for download",
                code="EXPORT_NOT_READY",
            )
        if not job.result_path:
            raise ConflictError(
                "Export file missing",
                code="EXPORT_FILE_MISSING",
            )
        path = Path(job.result_path)
        if not path.is_file():
            raise NotFoundError("Export file no longer available", code="NOT_FOUND")
        return path, job.format

    async def should_use_async(self, project_id: uuid.UUID, *, run_async: bool) -> bool:
        if run_async:
            return True
        n = await count_timeline_rows(self._session, project_id)
        return n >= self._settings.project_export_async_min_rows

    async def stream_csv(
        self,
        project_id: uuid.UUID,
        viewer: User,
    ) -> AsyncIterator[bytes]:
        await self._get_project_or_404(project_id)
        await self._assert_export_auth(project_id, viewer)
        bs = self._settings.project_export_batch_size
        async with AsyncSessionLocal() as stream_session:
            async for chunk in iter_csv_row_bytes(
                stream_session,
                project_id,
                batch_size=bs,
            ):
                yield chunk

    async def stream_json(
        self,
        project_id: uuid.UUID,
        viewer: User,
    ) -> AsyncIterator[bytes]:
        await self._get_project_or_404(project_id)
        await self._assert_export_auth(project_id, viewer)
        bs = self._settings.project_export_batch_size
        async with AsyncSessionLocal() as stream_session:
            async for chunk in iter_json_bundle_bytes(
                stream_session,
                project_id,
                batch_size=bs,
            ):
                yield chunk
