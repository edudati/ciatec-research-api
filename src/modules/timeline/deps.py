"""FastAPI dependencies for timeline APIs."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.database import get_db
from src.modules.timeline.runtime import get_timeline_redis
from src.modules.timeline.service import TimelineService


def get_timeline_service(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TimelineService:
    return TimelineService(db, settings=settings, redis=get_timeline_redis())
