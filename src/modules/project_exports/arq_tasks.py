"""arq worker task: generate project timeline export file."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from src.core.config import get_settings
from src.core.database import AsyncSessionLocal
from src.models.project_export_job import ProjectExportJob
from src.modules.project_exports.constants import (
    JOB_STATUS_COMPLETED,
    JOB_STATUS_FAILED,
    JOB_STATUS_QUEUED,
    JOB_STATUS_RUNNING,
)
from src.modules.project_exports.export_file import (
    resolve_export_storage_dir,
    write_export_to_path,
)

log = logging.getLogger(__name__)


async def generate_project_export(ctx: dict[str, Any], job_id_str: str) -> None:
    _ = ctx
    job_id = uuid.UUID(job_id_str)
    settings = get_settings()
    storage = resolve_export_storage_dir(settings)
    batch_size = settings.project_export_batch_size

    async with AsyncSessionLocal() as session:
        job = await session.get(ProjectExportJob, job_id)
        if job is None or job.status != JOB_STATUS_QUEUED:
            return
        project_id = job.project_id
        export_format = job.format
        job.status = JOB_STATUS_RUNNING
        await session.commit()

    path = storage / f"{job_id}.{export_format}"
    try:
        async with AsyncSessionLocal() as session:
            total = await write_export_to_path(
                session,
                project_id=project_id,
                path=path,
                export_format=export_format,
                batch_size=batch_size,
            )
        async with AsyncSessionLocal() as session:
            job_done = await session.get(ProjectExportJob, job_id)
            if job_done is None:
                return
            job_done.status = JOB_STATUS_COMPLETED
            job_done.row_count = total
            job_done.result_path = str(path.resolve())
            job_done.completed_at = datetime.now(UTC)
            await session.commit()
    except Exception:
        log.exception("project export job %s failed", job_id_str)
        async with AsyncSessionLocal() as session:
            job_fail = await session.get(ProjectExportJob, job_id)
            if job_fail is not None:
                job_fail.status = JOB_STATUS_FAILED
                job_fail.error_code = "EXPORT_FAILED"
                job_fail.error_message = "Export generation failed"
                job_fail.completed_at = datetime.now(UTC)
                await session.commit()
        if path.exists():
            try:
                path.unlink()
            except OSError:
                log.warning("could not remove failed export file %s", path)
