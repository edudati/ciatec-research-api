"""Catalog persistence."""

import uuid
from datetime import datetime

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models.catalog import Game, Level, Preset


class CatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, obj: Game | Preset | Level) -> None:
        self._session.add(obj)

    async def flush(self) -> None:
        await self._session.flush()

    async def refresh(self, obj: Game | Preset | Level) -> None:
        await self._session.refresh(obj)

    async def list_games_public(self) -> list[Game]:
        stmt = (
            select(Game)
            .where(Game.deleted_at.is_(None), Game.is_active.is_(True))
            .order_by(Game.name.asc())
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def list_games_admin(self) -> list[Game]:
        stmt = select(Game).order_by(Game.name.asc())
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_game(self, game_id: uuid.UUID) -> Game | None:
        stmt = select(Game).where(Game.id == game_id)
        return (await self._session.scalars(stmt)).first()

    async def get_game_by_slug(self, slug: str) -> Game | None:
        stmt = select(Game).where(
            Game.slug == slug,
            Game.deleted_at.is_(None),
        )
        return (await self._session.scalars(stmt)).first()

    async def list_presets_for_game_public(self, game_id: uuid.UUID) -> list[Preset]:
        stmt = (
            select(Preset)
            .join(Game, Preset.game_id == Game.id)
            .where(
                Preset.game_id == game_id,
                Preset.deleted_at.is_(None),
                Preset.is_active.is_(True),
                Game.deleted_at.is_(None),
                Game.is_active.is_(True),
            )
            .order_by(Preset.is_default.desc(), Preset.name.asc())
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def list_presets_for_game_admin(self, game_id: uuid.UUID) -> list[Preset]:
        stmt = (
            select(Preset)
            .where(Preset.game_id == game_id)
            .order_by(Preset.is_default.desc(), Preset.name.asc())
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_preset_with_game(self, preset_id: uuid.UUID) -> Preset | None:
        stmt = (
            select(Preset)
            .where(Preset.id == preset_id)
            .options(joinedload(Preset.game))
        )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def list_levels_for_preset_public(self, preset_id: uuid.UUID) -> list[Level]:
        stmt = (
            select(Level)
            .join(Preset, Level.preset_id == Preset.id)
            .join(Game, Preset.game_id == Game.id)
            .where(
                Level.preset_id == preset_id,
                Level.deleted_at.is_(None),
                Level.is_active.is_(True),
                Preset.deleted_at.is_(None),
                Preset.is_active.is_(True),
                Game.deleted_at.is_(None),
                Game.is_active.is_(True),
            )
            .order_by(Level.level_order.asc())
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def list_levels_for_preset_admin(self, preset_id: uuid.UUID) -> list[Level]:
        stmt = (
            select(Level)
            .where(Level.preset_id == preset_id)
            .order_by(Level.level_order.asc())
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_level_with_chain(self, level_id: uuid.UUID) -> Level | None:
        stmt = (
            select(Level)
            .where(Level.id == level_id)
            .options(joinedload(Level.preset).joinedload(Preset.game))
        )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def unset_all_defaults_for_game(self, game_id: uuid.UUID) -> None:
        await self._session.execute(
            update(Preset)
            .where(Preset.game_id == game_id, Preset.deleted_at.is_(None))
            .values(is_default=False)
        )

    async def unset_default_presets_except(
        self,
        game_id: uuid.UUID,
        keep_preset_id: uuid.UUID,
    ) -> None:
        await self._session.execute(
            update(Preset)
            .where(
                Preset.game_id == game_id,
                Preset.deleted_at.is_(None),
                Preset.id != keep_preset_id,
            )
            .values(is_default=False)
        )

    async def soft_delete_levels_for_preset(
        self,
        preset_id: uuid.UUID,
        when: datetime,
    ) -> None:
        await self._session.execute(
            update(Level)
            .where(Level.preset_id == preset_id, Level.deleted_at.is_(None))
            .values(deleted_at=when, is_active=False)
        )

    async def soft_delete_levels_for_game(
        self, game_id: uuid.UUID, when: datetime
    ) -> None:
        preset_ids = select(Preset.id).where(Preset.game_id == game_id)
        await self._session.execute(
            update(Level)
            .where(
                Level.preset_id.in_(preset_ids),
                Level.deleted_at.is_(None),
            )
            .values(deleted_at=when, is_active=False)
        )

    async def soft_delete_presets_for_game(
        self, game_id: uuid.UUID, when: datetime
    ) -> None:
        await self._session.execute(
            update(Preset)
            .where(
                Preset.game_id == game_id,
                Preset.deleted_at.is_(None),
            )
            .values(deleted_at=when, is_active=False)
        )

    async def soft_delete_game(self, game_id: uuid.UUID, when: datetime) -> None:
        await self._session.execute(
            update(Game)
            .where(Game.id == game_id, Game.deleted_at.is_(None))
            .values(deleted_at=when, is_active=False)
        )

    async def level_order_exists(
        self,
        preset_id: uuid.UUID,
        order: int,
        *,
        exclude_level_id: uuid.UUID | None,
    ) -> bool:
        conds = [
            Level.preset_id == preset_id,
            Level.deleted_at.is_(None),
            Level.level_order == order,
        ]
        if exclude_level_id is not None:
            conds.append(Level.id != exclude_level_id)
        stmt = select(Level.id).where(and_(*conds)).limit(1)
        row = (await self._session.scalars(stmt)).first()
        return row is not None
