"""Dependency providers for TrunkTilt telemetry."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.telemetry.trunktilt.service import TrunkTiltTelemetryService


def get_trunktilt_telemetry_service(
    db: AsyncSession = Depends(get_db),
) -> TrunkTiltTelemetryService:
    return TrunkTiltTelemetryService(db)
