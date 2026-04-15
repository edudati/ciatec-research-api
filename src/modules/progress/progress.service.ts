import type { PrismaClient } from '@prisma/client';

import { NotFoundError } from '../../shared/errors/not-found-error.js';

type ProgressServiceDeps = {
  prisma: PrismaClient;
};

export function createProgressService({ prisma }: ProgressServiceDeps) {
  return {
    async start(input: { userId: string; gameId: string }) {
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
          preset: { select: { id: true, name: true } },
          currentLevel: {
            select: { id: true, name: true, order: true, config: true },
          },
        },
      });

      if (!userGame) {
        const firstPreset = await prisma.preset.findFirst({
          where: { gameId: input.gameId },
          orderBy: { id: 'asc' },
          select: {
            id: true,
            name: true,
            levels: {
              orderBy: { order: 'asc' },
              take: 1,
              select: { id: true, name: true, order: true, config: true },
            },
          },
        });

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
            preset: { select: { id: true, name: true } },
            currentLevel: {
              select: { id: true, name: true, order: true, config: true },
            },
          },
        });
      }

      return {
        user_game_id: userGame.id,
        game: userGame.game,
        preset: userGame.preset,
        current_level: userGame.currentLevel,
      };
    },
  };
}

export type ProgressService = ReturnType<typeof createProgressService>;
