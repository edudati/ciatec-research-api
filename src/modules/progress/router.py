"""Progress endpoints: bootstrap state per game."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.modules.auth.deps import get_access_user_id
from src.modules.progress.deps import get_progress_service
from src.modules.progress.schemas import LevelsDetail, ProgressStartOut
from src.modules.progress.service import ProgressService

router = APIRouter(
    prefix="/api/v1/progress",
    tags=["Progress"],
    dependencies=[Depends(get_access_user_id)],
)


@router.get(
    "/start",
    response_model=ProgressStartOut,
    response_model_exclude_none=True,
    summary="Bootstrap progress for a game",
    description=(
        "Ensures a UserGame row exists (default preset, seeded unlocks), returns "
        "preset and levels. Use levels_detail=full to include each level's config "
        "JSON; summary omits config for a smaller payload."
    ),
)
async def progress_start(
    game_id: UUID = Query(..., description="Game UUID."),
    levels_detail: LevelsDetail = Query(
        "summary",
        description="`full` includes level config; `summary` omits it.",
    ),
    user_id: UUID = Depends(get_access_user_id),
    service: ProgressService = Depends(get_progress_service),
) -> ProgressStartOut:
    return await service.start(user_id, game_id, levels_detail)
