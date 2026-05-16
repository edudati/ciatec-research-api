"""Business logic for timeline read APIs."""

import uuid
from datetime import UTC, date, datetime, time

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings
from src.core.enums import UserRole
from src.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from src.models.timeline_event import TimelineEvent
from src.models.user import User
from src.modules.participants.repository import ParticipantsRepository
from src.modules.projects.repository import ProjectsRepository
from src.modules.timeline.cache_store import (
    cache_get_list,
    cache_set_list,
    timeline_list_cache_key,
)
from src.modules.timeline.repository import TimelineRepository
from src.modules.timeline.schemas import TimelineEventOut, TimelineListResponse


class TimelineService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        settings: Settings,
        redis: Redis | None,
    ) -> None:
        self._session = session
        self._repo = TimelineRepository(session)
        self._projects = ProjectsRepository(session)
        self._participants = ParticipantsRepository(session)
        self._settings = settings
        self._redis = redis

    def _use_timeline_cache(self) -> bool:
        return self._redis is not None and self._settings.timeline_cache_enabled

    @staticmethod
    def _dt_iso(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.isoformat()

    def _to_out(self, row: TimelineEvent) -> TimelineEventOut:
        return TimelineEventOut(
            id=str(row.id),
            participant_profile_id=str(row.participant_profile_id),
            project_id=str(row.project_id),
            enrollment_id=str(row.enrollment_id) if row.enrollment_id else None,
            executor_id=str(row.executor_id) if row.executor_id else None,
            event_type=row.event_type,
            source_type=row.source_type,
            source_id=row.source_id,
            occurred_at=self._dt_iso(row.occurred_at),
            context=dict(row.context),
            created_at=self._dt_iso(row.created_at),
        )

    @staticmethod
    def _occurred_bounds(
        from_date: date | None,
        to_date: date | None,
    ) -> tuple[datetime | None, datetime | None]:
        if from_date is not None and to_date is not None and from_date > to_date:
            raise ValidationError(
                "fromDate must be on or before toDate",
                code="VALIDATION_ERROR",
            )
        occurred_from = (
            datetime.combine(from_date, time.min, tzinfo=UTC)
            if from_date is not None
            else None
        )
        occurred_to = (
            datetime.combine(
                to_date,
                time(23, 59, 59, 999999, tzinfo=UTC),
            )
            if to_date is not None
            else None
        )
        return occurred_from, occurred_to

    async def _assert_can_view_project(self, project_id: uuid.UUID, user: User) -> None:
        row = await self._projects.get_project_public(project_id)
        if row is None:
            raise NotFoundError("Project not found", code="NOT_FOUND")
        if user.role == UserRole.ADMIN.value:
            return
        if await self._projects.user_has_any_membership(project_id, user.id):
            return
        raise ForbiddenError("Access denied to this project", code="FORBIDDEN")

    def _researcher_executor_scope(self, user: User) -> uuid.UUID | None:
        if user.role == UserRole.RESEARCHER.value:
            return user.id
        return None

    async def list_for_participant(
        self,
        participant_profile_id: uuid.UUID,
        *,
        _viewer: User,
        event_type: str | None,
        from_date: date | None,
        to_date: date | None,
        executor_id: uuid.UUID | None,
        page: int,
        page_size: int,
    ) -> TimelineListResponse:
        profile = await self._participants.get_active_by_id(participant_profile_id)
        if profile is None:
            raise NotFoundError("Participant profile not found", code="NOT_FOUND")
        occurred_from, occurred_to = self._occurred_bounds(from_date, to_date)
        if self._use_timeline_cache():
            assert self._redis is not None
            cache_key = timeline_list_cache_key(
                scope="participant",
                participant_profile_id=participant_profile_id,
                project_id=None,
                force_executor_id=None,
                event_type=event_type,
                executor_id=executor_id,
                occurred_from=occurred_from,
                occurred_to=occurred_to,
                page=page,
                page_size=page_size,
            )
            cached = await cache_get_list(self._redis, cache_key)
            if cached is not None:
                return cached
        total = await self._repo.count_filtered(
            participant_profile_id=participant_profile_id,
            project_id=None,
            force_executor_id=None,
            event_type=event_type,
            executor_id=executor_id,
            occurred_from=occurred_from,
            occurred_to=occurred_to,
        )
        rows = await self._repo.list_page_filtered(
            participant_profile_id=participant_profile_id,
            project_id=None,
            force_executor_id=None,
            event_type=event_type,
            executor_id=executor_id,
            occurred_from=occurred_from,
            occurred_to=occurred_to,
            page=page,
            page_size=page_size,
        )
        out = TimelineListResponse(
            items=[self._to_out(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
        )
        if self._use_timeline_cache():
            assert self._redis is not None
            await cache_set_list(
                self._redis,
                timeline_list_cache_key(
                    scope="participant",
                    participant_profile_id=participant_profile_id,
                    project_id=None,
                    force_executor_id=None,
                    event_type=event_type,
                    executor_id=executor_id,
                    occurred_from=occurred_from,
                    occurred_to=occurred_to,
                    page=page,
                    page_size=page_size,
                ),
                out,
                self._settings.timeline_cache_ttl_seconds,
            )
        return out

    async def list_for_project(
        self,
        project_id: uuid.UUID,
        *,
        viewer: User,
        event_type: str | None,
        from_date: date | None,
        to_date: date | None,
        executor_id: uuid.UUID | None,
        page: int,
        page_size: int,
    ) -> TimelineListResponse:
        await self._assert_can_view_project(project_id, viewer)
        force_exec = self._researcher_executor_scope(viewer)
        occurred_from, occurred_to = self._occurred_bounds(from_date, to_date)
        if self._use_timeline_cache():
            assert self._redis is not None
            cache_key = timeline_list_cache_key(
                scope="project",
                participant_profile_id=None,
                project_id=project_id,
                force_executor_id=force_exec,
                event_type=event_type,
                executor_id=executor_id,
                occurred_from=occurred_from,
                occurred_to=occurred_to,
                page=page,
                page_size=page_size,
            )
            cached = await cache_get_list(self._redis, cache_key)
            if cached is not None:
                return cached
        total = await self._repo.count_filtered(
            participant_profile_id=None,
            project_id=project_id,
            force_executor_id=force_exec,
            event_type=event_type,
            executor_id=executor_id,
            occurred_from=occurred_from,
            occurred_to=occurred_to,
        )
        rows = await self._repo.list_page_filtered(
            participant_profile_id=None,
            project_id=project_id,
            force_executor_id=force_exec,
            event_type=event_type,
            executor_id=executor_id,
            occurred_from=occurred_from,
            occurred_to=occurred_to,
            page=page,
            page_size=page_size,
        )
        out = TimelineListResponse(
            items=[self._to_out(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
        )
        if self._use_timeline_cache():
            assert self._redis is not None
            await cache_set_list(
                self._redis,
                timeline_list_cache_key(
                    scope="project",
                    participant_profile_id=None,
                    project_id=project_id,
                    force_executor_id=force_exec,
                    event_type=event_type,
                    executor_id=executor_id,
                    occurred_from=occurred_from,
                    occurred_to=occurred_to,
                    page=page,
                    page_size=page_size,
                ),
                out,
                self._settings.timeline_cache_ttl_seconds,
            )
        return out

    async def list_global(
        self,
        *,
        _viewer: User,
        event_type: str | None,
        from_date: date | None,
        to_date: date | None,
        executor_id: uuid.UUID | None,
        page: int,
        page_size: int,
    ) -> TimelineListResponse:
        occurred_from, occurred_to = self._occurred_bounds(from_date, to_date)
        if self._use_timeline_cache():
            assert self._redis is not None
            cache_key = timeline_list_cache_key(
                scope="global",
                participant_profile_id=None,
                project_id=None,
                force_executor_id=None,
                event_type=event_type,
                executor_id=executor_id,
                occurred_from=occurred_from,
                occurred_to=occurred_to,
                page=page,
                page_size=page_size,
            )
            cached = await cache_get_list(self._redis, cache_key)
            if cached is not None:
                return cached
        total = await self._repo.count_filtered(
            participant_profile_id=None,
            project_id=None,
            force_executor_id=None,
            event_type=event_type,
            executor_id=executor_id,
            occurred_from=occurred_from,
            occurred_to=occurred_to,
        )
        rows = await self._repo.list_page_filtered(
            participant_profile_id=None,
            project_id=None,
            force_executor_id=None,
            event_type=event_type,
            executor_id=executor_id,
            occurred_from=occurred_from,
            occurred_to=occurred_to,
            page=page,
            page_size=page_size,
        )
        out = TimelineListResponse(
            items=[self._to_out(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
        )
        if self._use_timeline_cache():
            assert self._redis is not None
            await cache_set_list(
                self._redis,
                timeline_list_cache_key(
                    scope="global",
                    participant_profile_id=None,
                    project_id=None,
                    force_executor_id=None,
                    event_type=event_type,
                    executor_id=executor_id,
                    occurred_from=occurred_from,
                    occurred_to=occurred_to,
                    page=page,
                    page_size=page_size,
                ),
                out,
                self._settings.timeline_cache_ttl_seconds,
            )
        return out
