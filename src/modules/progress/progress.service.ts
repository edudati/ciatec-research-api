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
        prisma.game.findUnique({ where: { id: input.gameId }, select: { id: true, name: true } }),
      ]);

      if (!user) {
        throw new NotFoundError('User not found');
      }
      if (!game) {
        throw new NotFoundError('Game not found');
      }

      let userGame = await prisma.userGame.findUnique({
        where: { userId_gameId: { userId: input.userId, gameId: input.gameId } },
        include: {
          game: { select: { id: true, name: true } },
          preset: { select: { id: true, name: true, description: true } },
          currentLevel: {
            select: { id: true, name: true, order: true, config: true },
          },
        },
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
          where: { gameId: input.gameId, isDefault: true },
          orderBy: { id: 'asc' },
          select: selectPreset,
        });
        if (!firstPreset) {
          firstPreset = await prisma.preset.findFirst({
            where: { gameId: input.gameId },
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
          include: {
            game: { select: { id: true, name: true } },
            preset: { select: { id: true, name: true, description: true } },
            currentLevel: {
              select: { id: true, name: true, order: true, config: true },
            },
          },
        });
      }

      await ensureFirstLevelUnlockedInPreset(prisma, input.userId, userGame.presetId);

      const allLevels = await prisma.level.findMany({
        where: { presetId: userGame.presetId },
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
        id: userGame.currentLevel.id,
        name: userGame.currentLevel.name,
        order: userGame.currentLevel.order,
        config: userGame.currentLevel.config,
        unlocked: currentRow?.unlocked ?? false,
        completed: currentRow?.completed ?? false,
        is_current: true,
        bests: asBestsObject(currentRow?.bests),
      };

      return {
        user_game_id: userGame.id,
        game: userGame.game,
        preset: {
          id: userGame.preset.id,
          name: userGame.preset.name,
          description: userGame.preset.description,
        },
        current_level: currentLevelOut,
        levels: allLevels.map((l) => buildTrailItem(l)),
      };
    },
  };
}

export type ProgressService = ReturnType<typeof createProgressService>;
