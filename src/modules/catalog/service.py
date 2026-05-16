"""Catalog business logic and transactions."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError
from src.models.catalog import Game, Level, Preset
from src.modules.catalog.repository import CatalogRepository
from src.modules.catalog.schemas import (
    GameAdminOut,
    GameCreate,
    GameOut,
    GamesAdminListResponse,
    GamesListResponse,
    GameUpdate,
    LevelAdminOut,
    LevelCreate,
    LevelOut,
    LevelsAdminListResponse,
    LevelsListResponse,
    LevelUpdate,
    PresetAdminOut,
    PresetCreate,
    PresetOut,
    PresetsAdminListResponse,
    PresetsListResponse,
    PresetUpdate,
)


def _now() -> datetime:
    return datetime.now(UTC)


class CatalogService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CatalogRepository(session)

    @staticmethod
    def _game_public_ok(game: Game) -> bool:
        return game.deleted_at is None and game.is_active

    @staticmethod
    def _preset_public_ok(preset: Preset) -> bool:
        return (
            preset.deleted_at is None
            and preset.is_active
            and CatalogService._game_public_ok(preset.game)
        )

    @staticmethod
    def _level_public_ok(level: Level) -> bool:
        return (
            level.deleted_at is None
            and level.is_active
            and CatalogService._preset_public_ok(level.preset)
        )

    def _to_game_out(self, game: Game) -> GameOut:
        return GameOut.model_validate(game)

    def _to_game_admin_out(self, game: Game) -> GameAdminOut:
        return GameAdminOut(
            id=game.id,
            name=game.name,
            slug=game.slug,
            description=game.description,
            is_active=game.is_active,
            is_deleted=game.deleted_at is not None,
            created_at=game.created_at,
            updated_at=game.updated_at,
        )

    def _to_preset_out(self, preset: Preset) -> PresetOut:
        return PresetOut(
            id=preset.id,
            game_id=preset.game_id,
            name=preset.name,
            description=preset.description,
            is_default=preset.is_default,
            is_active=preset.is_active,
            created_at=preset.created_at,
            updated_at=preset.updated_at,
        )

    def _to_preset_admin_out(self, preset: Preset) -> PresetAdminOut:
        return PresetAdminOut(
            id=preset.id,
            game_id=preset.game_id,
            name=preset.name,
            description=preset.description,
            is_default=preset.is_default,
            is_active=preset.is_active,
            is_deleted=preset.deleted_at is not None,
            created_at=preset.created_at,
            updated_at=preset.updated_at,
        )

    def _to_level_out(self, level: Level) -> LevelOut:
        return LevelOut(
            id=level.id,
            preset_id=level.preset_id,
            name=level.name,
            order=level.level_order,
            config=dict(level.config),
            is_active=level.is_active,
            created_at=level.created_at,
            updated_at=level.updated_at,
        )

    def _to_level_admin_out(self, level: Level) -> LevelAdminOut:
        return LevelAdminOut(
            id=level.id,
            preset_id=level.preset_id,
            name=level.name,
            order=level.level_order,
            config=dict(level.config),
            is_active=level.is_active,
            is_deleted=level.deleted_at is not None,
            created_at=level.created_at,
            updated_at=level.updated_at,
        )

    async def list_games_public(self) -> GamesListResponse:
        rows = await self._repo.list_games_public()
        return GamesListResponse(games=[self._to_game_out(g) for g in rows])

    async def list_games_admin(self) -> GamesAdminListResponse:
        rows = await self._repo.list_games_admin()
        return GamesAdminListResponse(games=[self._to_game_admin_out(g) for g in rows])

    async def get_game_public(self, game_id: uuid.UUID) -> GameOut:
        game = await self._repo.get_game(game_id)
        if game is None or not self._game_public_ok(game):
            raise NotFoundError("Game not found", code="GAME_NOT_FOUND")
        return self._to_game_out(game)

    async def get_game_admin(self, game_id: uuid.UUID) -> GameAdminOut:
        game = await self._repo.get_game(game_id)
        if game is None:
            raise NotFoundError("Game not found", code="GAME_NOT_FOUND")
        return self._to_game_admin_out(game)

    async def create_game_admin(self, body: GameCreate) -> GameAdminOut:
        game = await self._insert_game(body)
        return self._to_game_admin_out(game)

    async def _insert_game(self, body: GameCreate) -> Game:
        slug = CatalogService._normalize_game_slug(body.slug)
        game = Game(
            id=uuid.uuid4(),
            name=body.name.strip(),
            slug=slug,
            description=body.description,
            is_active=body.is_active,
        )
        self._repo.add(game)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ConflictError(
                "Game slug already in use", code="GAME_SLUG_CONFLICT"
            ) from exc
        await self._repo.refresh(game)
        return game

    @staticmethod
    def _normalize_game_slug(raw: str | None) -> str | None:
        if raw is None:
            return None
        s = raw.strip().lower()
        return s or None

    async def _mutate_game(self, game: Game, body: GameUpdate) -> None:
        incoming = body.model_dump(exclude_unset=True)
        if body.name is not None:
            game.name = body.name.strip()
        if "slug" in incoming:
            raw = incoming["slug"]
            game.slug = (
                CatalogService._normalize_game_slug(raw)
                if isinstance(raw, str)
                else None
            )
        if body.description is not None:
            game.description = body.description
        if body.is_active is not None:
            game.is_active = body.is_active
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ConflictError(
                "Game slug already in use", code="GAME_SLUG_CONFLICT"
            ) from exc
        await self._repo.refresh(game)

    async def update_game_admin(
        self, game_id: uuid.UUID, body: GameUpdate
    ) -> GameAdminOut:
        game = await self._repo.get_game(game_id)
        if game is None:
            raise NotFoundError("Game not found", code="GAME_NOT_FOUND")
        await self._mutate_game(game, body)
        return self._to_game_admin_out(game)

    async def delete_game_admin(self, game_id: uuid.UUID) -> None:
        game = await self._repo.get_game(game_id)
        if game is None:
            raise NotFoundError("Game not found", code="GAME_NOT_FOUND")
        if game.deleted_at is not None:
            return
        now = _now()
        await self._repo.soft_delete_levels_for_game(game_id, now)
        await self._repo.soft_delete_presets_for_game(game_id, now)
        await self._repo.soft_delete_game(game_id, now)
        await self._session.commit()

    async def list_presets_for_game_public(
        self, game_id: uuid.UUID
    ) -> PresetsListResponse:
        game = await self._repo.get_game(game_id)
        if game is None or not self._game_public_ok(game):
            raise NotFoundError("Game not found", code="GAME_NOT_FOUND")
        rows = await self._repo.list_presets_for_game_public(game_id)
        return PresetsListResponse(presets=[self._to_preset_out(p) for p in rows])

    async def list_presets_for_game_admin(
        self, game_id: uuid.UUID
    ) -> PresetsAdminListResponse:
        game = await self._repo.get_game(game_id)
        if game is None:
            raise NotFoundError("Game not found", code="GAME_NOT_FOUND")
        rows = await self._repo.list_presets_for_game_admin(game_id)
        return PresetsAdminListResponse(
            presets=[self._to_preset_admin_out(p) for p in rows]
        )

    async def get_preset_public(self, preset_id: uuid.UUID) -> PresetOut:
        preset = await self._repo.get_preset_with_game(preset_id)
        if preset is None or not self._preset_public_ok(preset):
            raise NotFoundError("Preset not found", code="PRESET_NOT_FOUND")
        return self._to_preset_out(preset)

    async def get_preset_admin(self, preset_id: uuid.UUID) -> PresetAdminOut:
        preset = await self._repo.get_preset_with_game(preset_id)
        if preset is None:
            raise NotFoundError("Preset not found", code="PRESET_NOT_FOUND")
        return self._to_preset_admin_out(preset)

    async def create_preset_admin(self, body: PresetCreate) -> PresetAdminOut:
        preset = await self._insert_preset(body)
        return self._to_preset_admin_out(preset)

    async def _insert_preset(self, body: PresetCreate) -> Preset:
        game = await self._repo.get_game(body.game_id)
        if game is None or game.deleted_at is not None:
            raise NotFoundError("Game not found", code="GAME_NOT_FOUND")

        if body.is_default:
            await self._repo.unset_all_defaults_for_game(body.game_id)

        preset = Preset(
            id=uuid.uuid4(),
            game_id=body.game_id,
            name=body.name.strip(),
            description=body.description,
            is_default=body.is_default,
            is_active=body.is_active,
        )
        self._repo.add(preset)
        await self._session.commit()
        await self._repo.refresh(preset)
        return preset

    async def _mutate_preset(self, preset: Preset, body: PresetUpdate) -> None:
        if body.name is not None:
            preset.name = body.name.strip()
        if body.description is not None:
            preset.description = body.description
        if body.is_active is not None:
            preset.is_active = body.is_active
        if body.is_default is not None:
            if body.is_default:
                await self._repo.unset_default_presets_except(preset.game_id, preset.id)
                preset.is_default = True
            else:
                preset.is_default = False
        await self._session.commit()
        await self._repo.refresh(preset)

    async def update_preset_admin(
        self, preset_id: uuid.UUID, body: PresetUpdate
    ) -> PresetAdminOut:
        preset = await self._repo.get_preset_with_game(preset_id)
        if preset is None:
            raise NotFoundError("Preset not found", code="PRESET_NOT_FOUND")
        await self._mutate_preset(preset, body)
        return self._to_preset_admin_out(preset)

    async def delete_preset_admin(self, preset_id: uuid.UUID) -> None:
        preset = await self._repo.get_preset_with_game(preset_id)
        if preset is None:
            raise NotFoundError("Preset not found", code="PRESET_NOT_FOUND")
        if preset.deleted_at is not None:
            return
        await self._soft_delete_preset(preset)

    async def _soft_delete_preset(self, preset: Preset) -> None:
        now = _now()
        await self._repo.soft_delete_levels_for_preset(preset.id, now)
        preset.deleted_at = now
        preset.is_active = False
        await self._session.commit()

    async def list_levels_for_preset_public(
        self, preset_id: uuid.UUID
    ) -> LevelsListResponse:
        preset = await self._repo.get_preset_with_game(preset_id)
        if preset is None or not self._preset_public_ok(preset):
            raise NotFoundError("Preset not found", code="PRESET_NOT_FOUND")
        rows = await self._repo.list_levels_for_preset_public(preset_id)
        return LevelsListResponse(levels=[self._to_level_out(x) for x in rows])

    async def list_levels_for_preset_admin(
        self, preset_id: uuid.UUID
    ) -> LevelsAdminListResponse:
        preset = await self._repo.get_preset_with_game(preset_id)
        if preset is None:
            raise NotFoundError("Preset not found", code="PRESET_NOT_FOUND")
        rows = await self._repo.list_levels_for_preset_admin(preset_id)
        return LevelsAdminListResponse(
            levels=[self._to_level_admin_out(x) for x in rows]
        )

    async def get_level_public(self, level_id: uuid.UUID) -> LevelOut:
        level = await self._repo.get_level_with_chain(level_id)
        if level is None or not self._level_public_ok(level):
            raise NotFoundError("Level not found", code="LEVEL_NOT_FOUND")
        return self._to_level_out(level)

    async def get_level_admin(self, level_id: uuid.UUID) -> LevelAdminOut:
        level = await self._repo.get_level_with_chain(level_id)
        if level is None:
            raise NotFoundError("Level not found", code="LEVEL_NOT_FOUND")
        return self._to_level_admin_out(level)

    async def create_level_admin(self, body: LevelCreate) -> LevelAdminOut:
        level = await self._insert_level(body)
        return self._to_level_admin_out(level)

    @staticmethod
    def _preset_admin_attach_ok(preset: Preset) -> bool:
        return preset.deleted_at is None and preset.game.deleted_at is None

    async def _insert_level(self, body: LevelCreate) -> Level:
        preset = await self._repo.get_preset_with_game(body.preset_id)
        if preset is None:
            raise NotFoundError("Preset not found", code="PRESET_NOT_FOUND")
        if not self._preset_admin_attach_ok(preset):
            raise NotFoundError("Preset not found", code="PRESET_NOT_FOUND")

        if await self._repo.level_order_exists(
            body.preset_id, body.order, exclude_level_id=None
        ):
            raise ConflictError(
                "Level order already in use for this preset",
                code="LEVEL_ORDER_CONFLICT",
            )

        level = Level(
            id=uuid.uuid4(),
            preset_id=body.preset_id,
            name=body.name.strip(),
            level_order=body.order,
            config=dict(body.config),
            is_active=body.is_active,
        )
        self._repo.add(level)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ConflictError(
                "Level order already in use for this preset",
                code="LEVEL_ORDER_CONFLICT",
            ) from exc
        await self._session.commit()
        await self._repo.refresh(level)
        return level

    async def _mutate_level(self, level: Level, body: LevelUpdate) -> None:
        if body.name is not None:
            level.name = body.name.strip()
        if body.is_active is not None:
            level.is_active = body.is_active
        if body.config is not None:
            level.config = dict(body.config)
        if body.order is not None:
            if await self._repo.level_order_exists(
                level.preset_id,
                body.order,
                exclude_level_id=level.id,
            ):
                raise ConflictError(
                    "Level order already in use for this preset",
                    code="LEVEL_ORDER_CONFLICT",
                )
            level.level_order = body.order
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ConflictError(
                "Level order already in use for this preset",
                code="LEVEL_ORDER_CONFLICT",
            ) from exc
        await self._session.commit()
        await self._repo.refresh(level)

    async def update_level_admin(
        self, level_id: uuid.UUID, body: LevelUpdate
    ) -> LevelAdminOut:
        level = await self._repo.get_level_with_chain(level_id)
        if level is None:
            raise NotFoundError("Level not found", code="LEVEL_NOT_FOUND")
        await self._mutate_level(level, body)
        return self._to_level_admin_out(level)

    async def delete_level_admin(self, level_id: uuid.UUID) -> None:
        level = await self._repo.get_level_with_chain(level_id)
        if level is None:
            raise NotFoundError("Level not found", code="LEVEL_NOT_FOUND")
        if level.deleted_at is not None:
            return
        await self._soft_delete_level(level)

    async def _soft_delete_level(self, level: Level) -> None:
        now = _now()
        level.deleted_at = now
        level.is_active = False
        await self._session.commit()
