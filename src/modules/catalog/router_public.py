"""Public catalog routes (read-only filtered catalog)."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.auth.deps import get_access_user_id
from src.modules.catalog.schemas import (
    GameOut,
    GamesListResponse,
    LevelOut,
    LevelsListResponse,
    PresetOut,
    PresetsListResponse,
)
from src.modules.catalog.service import CatalogService


def get_catalog_service(db: AsyncSession = Depends(get_db)) -> CatalogService:
    return CatalogService(db)


router = APIRouter(
    prefix="/api/v1/catalog",
    tags=["Catalog"],
    dependencies=[Depends(get_access_user_id)],
)


@router.get("/games", response_model=GamesListResponse)
async def list_games(
    service: CatalogService = Depends(get_catalog_service),
) -> GamesListResponse:
    return await service.list_games_public()


@router.get("/games/{game_id}", response_model=GameOut)
async def get_game(
    game_id: UUID,
    service: CatalogService = Depends(get_catalog_service),
) -> GameOut:
    return await service.get_game_public(game_id)


@router.get("/games/{game_id}/presets", response_model=PresetsListResponse)
async def list_presets_for_game(
    game_id: UUID,
    service: CatalogService = Depends(get_catalog_service),
) -> PresetsListResponse:
    return await service.list_presets_for_game_public(game_id)


@router.get("/presets/{preset_id}", response_model=PresetOut)
async def get_preset(
    preset_id: UUID,
    service: CatalogService = Depends(get_catalog_service),
) -> PresetOut:
    return await service.get_preset_public(preset_id)


@router.get("/presets/{preset_id}/levels", response_model=LevelsListResponse)
async def list_levels_for_preset(
    preset_id: UUID,
    service: CatalogService = Depends(get_catalog_service),
) -> LevelsListResponse:
    return await service.list_levels_for_preset_public(preset_id)


@router.get("/levels/{level_id}", response_model=LevelOut)
async def get_level(
    level_id: UUID,
    service: CatalogService = Depends(get_catalog_service),
) -> LevelOut:
    return await service.get_level_public(level_id)
