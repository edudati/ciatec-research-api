"""Write timeline export files (HTTP streaming and arq worker)."""

from __future__ import annotations

import csv
import json
import tempfile
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings
from src.models.project import Project
from src.models.timeline_event import TimelineEvent
from src.modules.project_exports.constants import CSV_HEADERS, SCHEMA_VERSION
from src.modules.projects.repository import ProjectsRepository
from src.modules.timeline.repository import TimelineRepository
from src.modules.timeline.schemas import TimelineEventOut


def _dt_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()


def timeline_row_to_out(row: TimelineEvent) -> TimelineEventOut:
    return TimelineEventOut(
        id=str(row.id),
        participant_profile_id=str(row.participant_profile_id),
        project_id=str(row.project_id),
        enrollment_id=str(row.enrollment_id) if row.enrollment_id else None,
        executor_id=str(row.executor_id) if row.executor_id else None,
        event_type=row.event_type,
        source_type=row.source_type,
        source_id=row.source_id,
        occurred_at=_dt_iso(row.occurred_at),
        context=dict(row.context),
        created_at=_dt_iso(row.created_at),
    )


def _project_snapshot(project: Project) -> dict[str, Any]:
    return {
        "id": str(project.id),
        "code": project.code,
        "name": project.name,
        "status": project.status,
        "startDate": project.start_date.isoformat() if project.start_date else None,
        "endDate": project.end_date.isoformat() if project.end_date else None,
    }


async def count_timeline_rows(session: AsyncSession, project_id: uuid.UUID) -> int:
    repo = TimelineRepository(session)
    return await repo.count_by_project(project_id)


async def iter_csv_row_bytes(
    session: AsyncSession,
    project_id: uuid.UUID,
    *,
    batch_size: int,
) -> AsyncIterator[bytes]:
    import io

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(CSV_HEADERS)
    yield buf.getvalue().encode("utf-8")
    buf.seek(0)
    buf.truncate(0)

    repo = TimelineRepository(session)
    async for batch in repo.iter_project_events_batches(
        project_id,
        batch_size=batch_size,
    ):
        for row in batch:
            out = timeline_row_to_out(row)
            writer.writerow(
                [
                    out.id,
                    out.participant_profile_id,
                    out.project_id,
                    out.enrollment_id or "",
                    out.executor_id or "",
                    out.event_type,
                    out.source_type,
                    out.source_id,
                    out.occurred_at,
                    json.dumps(out.context, ensure_ascii=False, sort_keys=True),
                    out.created_at,
                ],
            )
            yield buf.getvalue().encode("utf-8")
            buf.seek(0)
            buf.truncate(0)


async def iter_json_bundle_bytes(
    session: AsyncSession,
    project_id: uuid.UUID,
    *,
    batch_size: int,
) -> AsyncIterator[bytes]:
    projects_repo = ProjectsRepository(session)
    project = await projects_repo.get_project_public(project_id)
    if project is None:
        msg = "Project not found"
        raise ValueError(msg)

    exported_at = datetime.now(UTC).isoformat()
    head = {
        "schemaVersion": SCHEMA_VERSION,
        "exportedAt": exported_at,
        "project": _project_snapshot(project),
    }
    head_txt = json.dumps(head, ensure_ascii=False)
    yield (head_txt[:-1] + ',"timeline":[').encode("utf-8")

    first = True
    repo = TimelineRepository(session)
    async for batch in repo.iter_project_events_batches(
        project_id,
        batch_size=batch_size,
    ):
        for row in batch:
            ev = timeline_row_to_out(row)
            payload = ev.model_dump(mode="json", by_alias=True)
            chunk = json.dumps(payload, ensure_ascii=False)
            if first:
                yield chunk.encode("utf-8")
                first = False
            else:
                yield ("," + chunk).encode("utf-8")
    yield b"]}"


async def write_export_to_path(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    path: Path,
    export_format: str,
    batch_size: int,
) -> int:
    """Writes full export file; returns number of timeline rows."""
    path.parent.mkdir(parents=True, exist_ok=True)
    repo = TimelineRepository(session)
    total = await repo.count_by_project(project_id)
    if export_format == "csv":
        with path.open("wb") as f:
            async for chunk in iter_csv_row_bytes(
                session,
                project_id,
                batch_size=batch_size,
            ):
                f.write(chunk)
    elif export_format == "json":
        with path.open("wb") as f:
            async for chunk in iter_json_bundle_bytes(
                session,
                project_id,
                batch_size=batch_size,
            ):
                f.write(chunk)
    else:
        msg = f"Unsupported export format: {export_format!r}"
        raise ValueError(msg)
    return total


def resolve_export_storage_dir(settings: Settings) -> Path:
    if settings.project_export_storage_dir:
        return Path(settings.project_export_storage_dir).expanduser().resolve()
    return Path(tempfile.gettempdir()) / "ciatec_project_exports"
