"""Dependency providers for Bestbeat telemetry."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.telemetry.bestbeat.service import BestbeatTelemetryService


def get_bestbeat_telemetry_service(
    db: AsyncSession = Depends(get_db),
) -> BestbeatTelemetryService:
    return BestbeatTelemetryService(db)
