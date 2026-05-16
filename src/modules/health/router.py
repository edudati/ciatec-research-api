from fastapi import APIRouter, HTTPException

from src.modules.health.schemas import HealthOut
from src.modules.health.service import ping_database

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut, response_model_by_alias=True)
async def health() -> HealthOut:
    try:
        await ping_database()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="database_unavailable",
        ) from exc
    return HealthOut.with_timeline_metrics()
