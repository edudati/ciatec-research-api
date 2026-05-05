import { Prisma, type PrismaClient, type UserGame, type UserLevelProgress } from '@prisma/client';

import { NotFoundError } from '../../shared/errors/not-found-error.js';

import { assertLevelUnlockedForUser, ensureFirstLevelUnlockedInPreset } from './user-level-progress-helpers.js';

type ProgressServiceDeps = {
  prisma: PrismaClient;
};

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

type UserGameWithRelations = UserGame & {
  game: { id: string; name: string };
  preset: { id: string; name: string; description: string | null };
  currentLevel: { id: string; name: string; order: number };
};

const userGameInclude = {
  game: { select: { id: true, name: true } },
  preset: { select: { id: true, name: true, description: true } },
  currentLevel: { select: { id: true, name: true, order: true } },
} as const;

async function ensureUserGameForGame(
  prisma: PrismaClient,
  userId: string,
  gameId: string,
): Promise<UserGameWithRelations> {
  const [user, game] = await Promise.all([
    prisma.user.findUnique({ where: { id: userId }, select: { id: true } }),
    prisma.game.findUnique({ where: { id: gameId }, select: { id: true, name: true } }),
  ]);

  if (!user) {
    throw new NotFoundError('User not found');
  }
  if (!game) {
    throw new NotFoundError('Game not found');
  }

  let userGame = await prisma.userGame.findUnique({
    where: { userId_gameId: { userId, gameId } },
    include: userGameInclude,
  });

  if (!userGame) {
    const selectPreset = {
      id: true,
      name: true,
      description: true,
      levels: {
        orderBy: { order: 'asc' as const },
        take: 1,
        select: { id: true, name: true, order: true },
      },
    };

    let firstPreset = await prisma.preset.findFirst({
      where: { gameId, isDefault: true },
      orderBy: { id: 'asc' },
      select: selectPreset,
    });
    if (!firstPreset) {
      firstPreset = await prisma.preset.findFirst({
        where: { gameId },
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
        userId,
        gameId,
        presetId: firstPreset.id,
        currentLevelId: firstLevel.id,
      },
      include: userGameInclude,
    });
  }

  await ensureFirstLevelUnlockedInPreset(prisma, userId, userGame.presetId);

  return userGame;
}

export function createProgressService({ prisma }: ProgressServiceDeps) {
  return {
    async getPreset(input: { userId: string; gameId: string }) {
      const userGame = await ensureUserGameForGame(prisma, input.userId, input.gameId);

      const allLevels = await prisma.level.findMany({
        where: { presetId: userGame.presetId },
        orderBy: { order: 'asc' },
        select: { id: true, name: true, order: true },
      });

      const levelIds = allLevels.map((l) => l.id);
      const progressRows =
        levelIds.length === 0
          ? []
          : await prisma.userLevelProgress.findMany({
              where: { userId: input.userId, levelId: { in: levelIds } },
            });
      const pMap = new Map<string, UserLevelProgress>(progressRows.map((r) => [r.levelId, r]));

      const buildTrailItem = (level: { id: string; name: string; order: number }) => {
        const row = pMap.get(level.id);
        return {
          id: level.id,
          name: level.name,
          order: level.order,
          unlocked: row?.unlocked ?? false,
          completed: row?.completed ?? false,
          is_current: level.id === userGame.currentLevelId,
          bests: asBestsObject(row?.bests),
        };
      };

      const currentRow = pMap.get(userGame.currentLevelId);
      const currentLevelOut = {
        id: userGame.currentLevel.id,
        name: userGame.currentLevel.name,
        order: userGame.currentLevel.order,
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

    async getLevel(input: { userId: string; levelId: string }) {
      const level = await prisma.level.findUnique({
        where: { id: input.levelId },
        select: {
          id: true,
          presetId: true,
          name: true,
          order: true,
          config: true,
          preset: { select: { gameId: true } },
        },
      });

      if (!level) {
        throw new NotFoundError('Level not found');
      }

      const gameId = level.preset.gameId;
      const userGame = await ensureUserGameForGame(prisma, input.userId, gameId);

      if (level.presetId !== userGame.presetId) {
        throw new NotFoundError('Level not found');
      }

      await assertLevelUnlockedForUser(prisma, input.userId, input.levelId);

      const row = await prisma.userLevelProgress.findUnique({
        where: { userId_levelId: { userId: input.userId, levelId: input.levelId } },
      });

      return {
        id: level.id,
        preset_id: level.presetId,
        game_id: gameId,
        name: level.name,
        order: level.order,
        config: level.config,
        unlocked: row?.unlocked ?? false,
        completed: row?.completed ?? false,
        bests: asBestsObject(row?.bests),
      };
    },
  };
}

export type ProgressService = ReturnType<typeof createProgressService>;
