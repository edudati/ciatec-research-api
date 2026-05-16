"""Admin catalog routes and Node-parity catalog writes under /api/v1/catalog."""

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.auth.deps import require_admin
from src.modules.catalog.schemas import (
    GameAdminOut,
    GameCreate,
    GamesAdminListResponse,
    GameUpdate,
    LevelAdminOut,
    LevelCreate,
    LevelsAdminListResponse,
    LevelUpdate,
    PresetAdminOut,
    PresetCreate,
    PresetsAdminListResponse,
    PresetUpdate,
)
from src.modules.catalog.service import CatalogService


def get_catalog_service(db: AsyncSession = Depends(get_db)) -> CatalogService:
    return CatalogService(db)


_admin = [Depends(require_admin)]

catalog_admin_reads = APIRouter(dependencies=_admin)


@catalog_admin_reads.get("/games", response_model=GamesAdminListResponse)
async def list_games(
    service: CatalogService = Depends(get_catalog_service),
) -> GamesAdminListResponse:
    return await service.list_games_admin()


@catalog_admin_reads.get("/games/{game_id}", response_model=GameAdminOut)
async def get_game(
    game_id: UUID,
    service: CatalogService = Depends(get_catalog_service),
) -> GameAdminOut:
    return await service.get_game_admin(game_id)


@catalog_admin_reads.get(
    "/games/{game_id}/presets",
    response_model=PresetsAdminListResponse,
)
async def list_presets_for_game(
    game_id: UUID,
    service: CatalogService = Depends(get_catalog_service),
) -> PresetsAdminListResponse:
    return await service.list_presets_for_game_admin(game_id)


@catalog_admin_reads.get("/presets/{preset_id}", response_model=PresetAdminOut)
async def get_preset(
    preset_id: UUID,
    service: CatalogService = Depends(get_catalog_service),
) -> PresetAdminOut:
    return await service.get_preset_admin(preset_id)


@catalog_admin_reads.get(
    "/presets/{preset_id}/levels",
    response_model=LevelsAdminListResponse,
)
async def list_levels_for_preset(
    preset_id: UUID,
    service: CatalogService = Depends(get_catalog_service),
) -> LevelsAdminListResponse:
    return await service.list_levels_for_preset_admin(preset_id)


@catalog_admin_reads.get("/levels/{level_id}", response_model=LevelAdminOut)
async def get_level(
    level_id: UUID,
    service: CatalogService = Depends(get_catalog_service),
) -> LevelAdminOut:
    return await service.get_level_admin(level_id)


catalog_admin_mutations = APIRouter(dependencies=_admin)


@catalog_admin_mutations.post(
    "/games",
    response_model=GameAdminOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_game(
    body: GameCreate,
    service: CatalogService = Depends(get_catalog_service),
) -> GameAdminOut:
    return await service.create_game_admin(body)


@catalog_admin_mutations.patch("/games/{game_id}", response_model=GameAdminOut)
async def patch_game(
    game_id: UUID,
    body: GameUpdate,
    service: CatalogService = Depends(get_catalog_service),
) -> GameAdminOut:
    return await service.update_game_admin(game_id, body)


@catalog_admin_mutations.delete(
    "/games/{game_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_game(
    game_id: UUID,
    service: CatalogService = Depends(get_catalog_service),
) -> Response:
    await service.delete_game_admin(game_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@catalog_admin_mutations.post(
    "/presets",
    response_model=PresetAdminOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_preset(
    body: PresetCreate,
    service: CatalogService = Depends(get_catalog_service),
) -> PresetAdminOut:
    return await service.create_preset_admin(body)


@catalog_admin_mutations.patch("/presets/{preset_id}", response_model=PresetAdminOut)
async def patch_preset(
    preset_id: UUID,
    body: PresetUpdate,
    service: CatalogService = Depends(get_catalog_service),
) -> PresetAdminOut:
    return await service.update_preset_admin(preset_id, body)


@catalog_admin_mutations.delete(
    "/presets/{preset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_preset(
    preset_id: UUID,
    service: CatalogService = Depends(get_catalog_service),
) -> Response:
    await service.delete_preset_admin(preset_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@catalog_admin_mutations.post(
    "/levels",
    response_model=LevelAdminOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_level(
    body: LevelCreate,
    service: CatalogService = Depends(get_catalog_service),
) -> LevelAdminOut:
    return await service.create_level_admin(body)


@catalog_admin_mutations.patch("/levels/{level_id}", response_model=LevelAdminOut)
async def patch_level(
    level_id: UUID,
    body: LevelUpdate,
    service: CatalogService = Depends(get_catalog_service),
) -> LevelAdminOut:
    return await service.update_level_admin(level_id, body)


@catalog_admin_mutations.delete(
    "/levels/{level_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_level(
    level_id: UUID,
    service: CatalogService = Depends(get_catalog_service),
) -> Response:
    await service.delete_level_admin(level_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


router = APIRouter(prefix="/api/v1/admin/catalog", tags=["Admin Catalog"])
router.include_router(catalog_admin_reads)
router.include_router(catalog_admin_mutations)

catalog_node_mirror_router = APIRouter(prefix="/api/v1/catalog", tags=["Catalog"])
catalog_node_mirror_router.include_router(catalog_admin_mutations)
