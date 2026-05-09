import { Prisma, type PrismaClient, type UserLevelProgress } from '@prisma/client';

import { NotFoundError } from '../../shared/errors/not-found-error.js';

import { ensureFirstLevelUnlockedInPreset } from './user-level-progress-helpers.js';

type ProgressServiceDeps = {
  prisma: PrismaClient;
};

type LevelsDetail = 'summary' | 'full';

function asBestsObject(value: Prisma.JsonValue | null | undefined): Prisma.JsonObject {
  if (value == null) {
    return {};
  }
  if (typeof value === 'string') {
    return {};
  }
  if (typeof value === 'object' && !Array.isArray(value)) {
    return value as Prisma.JsonObject;
  }
  return {};
}

export function createProgressService({ prisma }: ProgressServiceDeps) {
  return {
    async start(input: { userId: string; gameId: string; levelsDetail: LevelsDetail }) {
      const [user, game] = await Promise.all([
        prisma.user.findUnique({ where: { id: input.userId }, select: { id: true } }),
        prisma.game.findFirst({
          where: { id: input.gameId, isActive: true, isDeleted: false },
          select: { id: true, name: true },
        }),
      ]);

      if (!user) {
        throw new NotFoundError('User not found');
      }
      if (!game) {
        throw new NotFoundError('Game not found');
      }

      let userGame = await prisma.userGame.findUnique({
        where: { userId_gameId: { userId: input.userId, gameId: input.gameId } },
        select: { id: true, gameId: true, presetId: true, currentLevelId: true },
      });

      if (!userGame) {
        const selectPreset = {
          id: true,
          name: true,
          description: true,
          levels: {
            orderBy: { order: 'asc' as const },
            take: 1,
            select: { id: true, name: true, order: true, config: true },
          },
        };

        let firstPreset = await prisma.preset.findFirst({
          where: { gameId: input.gameId, isDefault: true, isActive: true, isDeleted: false, game: { isActive: true, isDeleted: false } },
          orderBy: { id: 'asc' },
          select: selectPreset,
        });
        if (!firstPreset) {
          firstPreset = await prisma.preset.findFirst({
            where: { gameId: input.gameId, isActive: true, isDeleted: false, game: { isActive: true, isDeleted: false } },
            orderBy: { id: 'asc' },
            select: selectPreset,
          });
        }

        if (!firstPreset) {
          throw new NotFoundError('No preset found for this game');
        }

        const firstLevel = firstPreset.levels[0];
        if (!firstLevel) {
          throw new NotFoundError('No level found for the selected preset');
        }

        userGame = await prisma.userGame.create({
          data: {
            userId: input.userId,
            gameId: input.gameId,
            presetId: firstPreset.id,
            currentLevelId: firstLevel.id,
          },
          select: { id: true, gameId: true, presetId: true, currentLevelId: true },
        });
      }

      await ensureFirstLevelUnlockedInPreset(prisma, input.userId, userGame.presetId);

      const [preset, currentLevel] = await Promise.all([
        prisma.preset.findFirst({
          where: { id: userGame.presetId, isActive: true, isDeleted: false, game: { isActive: true, isDeleted: false } },
          select: { id: true, name: true, description: true },
        }),
        prisma.level.findFirst({
          where: { id: userGame.currentLevelId, presetId: userGame.presetId, isActive: true, isDeleted: false, preset: { isActive: true, isDeleted: false, game: { isActive: true, isDeleted: false } } },
          select: { id: true, name: true, order: true, config: true },
        }),
      ]);

      if (!preset) {
        throw new NotFoundError('Preset not found');
      }
      if (!currentLevel) {
        throw new NotFoundError('Current level not found');
      }

      const allLevels = await prisma.level.findMany({
        where: { presetId: userGame.presetId, isActive: true, isDeleted: false, preset: { isActive: true, isDeleted: false, game: { isActive: true, isDeleted: false } } },
        orderBy: { order: 'asc' },
        select:
          input.levelsDetail === 'full'
            ? { id: true, name: true, order: true, config: true }
            : { id: true, name: true, order: true },
      });

      const levelIds = allLevels.map((l) => l.id);
      const progressRows =
        levelIds.length === 0
          ? []
          : await prisma.userLevelProgress.findMany({
              where: { userId: input.userId, levelId: { in: levelIds } },
            });
      const pMap = new Map<string, UserLevelProgress>(progressRows.map((r) => [r.levelId, r]));

      const buildTrailItem = (level: { id: string; name: string; order: number; config?: Prisma.JsonValue }) => {
        const row = pMap.get(level.id);
        return {
          id: level.id,
          name: level.name,
          order: level.order,
          unlocked: row?.unlocked ?? false,
          completed: row?.completed ?? false,
          is_current: level.id === userGame.currentLevelId,
          bests: asBestsObject(row?.bests),
          ...(input.levelsDetail === 'full' && 'config' in level && level.config !== undefined
            ? { config: level.config as Prisma.JsonValue }
            : {}),
        };
      };

      const currentRow = pMap.get(userGame.currentLevelId);
      const currentLevelOut = {
        id: currentLevel.id,
        name: currentLevel.name,
        order: currentLevel.order,
        config: currentLevel.config,
        unlocked: currentRow?.unlocked ?? false,
        completed: currentRow?.completed ?? false,
        is_current: true,
        bests: asBestsObject(currentRow?.bests),
      };

      return {
        user_game_id: userGame.id,
        game: { id: game.id, name: game.name },
        preset: {
          id: preset.id,
          name: preset.name,
          description: preset.description,
        },
        current_level: currentLevelOut,
        levels: allLevels.map((l) => buildTrailItem(l)),
      };
    },
  };
}

export type ProgressService = ReturnType<typeof createProgressService>;
