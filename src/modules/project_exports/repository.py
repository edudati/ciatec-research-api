"""Persistence for project_export_jobs."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.project_export_job import ProjectExportJob


class ProjectExportsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add_job(self, row: ProjectExportJob) -> None:
        self._session.add(row)

    async def get_job_for_project(
        self,
        project_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> ProjectExportJob | None:
        stmt = select(ProjectExportJob).where(
            ProjectExportJob.id == job_id,
            ProjectExportJob.project_id == project_id,
        )
        row = await self._session.execute(stmt)
        return row.scalar_one_or_none()

    async def get_job_by_id(self, job_id: uuid.UUID) -> ProjectExportJob | None:
        return await self._session.get(ProjectExportJob, job_id)
