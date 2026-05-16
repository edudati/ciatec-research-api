"""Bootstrap user progress for a game (preset, unlocks, current level)."""

import uuid
from collections.abc import Mapping
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.modules.catalog.repository import CatalogRepository
from src.modules.matches.repository import MatchRepository
from src.modules.matches.service import MatchesService
from src.modules.progress.schemas import (
    LevelsDetail,
    ProgressCurrentLevelOut,
    ProgressGameSummary,
    ProgressLevelTrailOut,
    ProgressPresetSummaryOut,
    ProgressStartOut,
)


class ProgressService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._matches_service = MatchesService(session)
        self._matches_repo = MatchRepository(session)
        self._catalog = CatalogRepository(session)

    @staticmethod
    def _level_config(level_config: object) -> dict[str, Any]:
        if isinstance(level_config, Mapping):
            return dict(level_config)
        return {}

    async def start(
        self,
        user_id: uuid.UUID,
        game_id: uuid.UUID,
        levels_detail: LevelsDetail,
    ) -> ProgressStartOut:
        user_game = await self._matches_service.ensure_user_game_and_seed_progress(
            user_id, game_id
        )

        preset = await self._catalog.get_preset_with_game(user_game.preset_id)
        if preset is None:
            raise NotFoundError("Preset not found", code="PRESET_NOT_FOUND")

        levels = await self._catalog.list_levels_for_preset_public(user_game.preset_id)
        progress_rows = await self._matches_repo.list_user_level_progress_for_preset(
            user_id, user_game.preset_id
        )
        unlock_by = {row.level_id: row.unlocked for row in progress_rows}

        current_level_id = user_game.current_level_id
        if not unlock_by.get(current_level_id, False):
            replacement: uuid.UUID | None = None
            for lvl in levels:
                if unlock_by.get(lvl.id, False):
                    replacement = lvl.id
                    break
            if replacement is not None:
                await self._matches_repo.update_user_game_current_level(
                    user_game.id, replacement
                )
                await self._session.commit()
                current_level_id = replacement

        current_level_row = next(
            (lvl for lvl in levels if lvl.id == current_level_id),
            levels[0],
        )

        trail: list[ProgressLevelTrailOut] = []
        for lvl in levels:
            cfg: dict[str, Any] | None = (
                self._level_config(lvl.config) if levels_detail == "full" else None
            )
            is_curr = lvl.id == current_level_id
            trail.append(
                ProgressLevelTrailOut(
                    id=lvl.id,
                    preset_id=lvl.preset_id,
                    name=lvl.name,
                    order=lvl.level_order,
                    config=cfg,
                    unlocked=bool(unlock_by.get(lvl.id, False)),
                    completed=False,
                    is_current=is_curr,
                    bests={},
                )
            )

        current_level = ProgressCurrentLevelOut(
            id=current_level_row.id,
            name=current_level_row.name,
            order=current_level_row.level_order,
            config=self._level_config(current_level_row.config),
            unlocked=bool(unlock_by.get(current_level_row.id, False)),
            completed=False,
            is_current=True,
            bests={},
        )

        game = preset.game

        return ProgressStartOut(
            user_game_id=user_game.id,
            game=ProgressGameSummary(id=game.id, name=game.name),
            preset=ProgressPresetSummaryOut(
                id=preset.id,
                name=preset.name,
                description=preset.description,
            ),
            current_level=current_level,
            levels=trail,
        )
