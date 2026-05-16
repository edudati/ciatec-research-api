"""Dependency providers for Bubbles telemetry."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.telemetry.bubbles.service import BubblesTelemetryService


def get_bubbles_telemetry_service(
    db: AsyncSession = Depends(get_db),
) -> BubblesTelemetryService:
    return BubblesTelemetryService(db)
