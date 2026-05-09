import { Prisma, type PrismaClient } from '@prisma/client';

import { assertLevelUnlockedForUser } from '../progress/user-level-progress-helpers.js';
import { NotFoundError } from '../../shared/errors/not-found-error.js';

type SessionsServiceDeps = {
  prisma: PrismaClient;
};

function toJsonSnapshot(config: Prisma.JsonValue | typeof Prisma.JsonNull): Prisma.InputJsonValue | typeof Prisma.JsonNull {
  if (config === null || config === Prisma.JsonNull) {
    return Prisma.JsonNull;
  }
  return JSON.parse(JSON.stringify(config)) as Prisma.InputJsonValue;
}

export function createSessionsService({ prisma }: SessionsServiceDeps) {
  const dayStartUtc = (): Date => {
    const now = new Date();
    return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
  };

  const dayEndUtc = (): Date => {
    const start = dayStartUtc();
    return new Date(start.getTime() + 24 * 60 * 60 * 1000);
  };

  async function ensureDailySession(userId: string) {
    const startDate = dayStartUtc();
    const created = await prisma.session.upsert({
      where: {
        userId_sessionDate: {
          userId,
          sessionDate: startDate,
        },
      },
      update: {},
      create: {
        userId,
        sessionDate: startDate,
      },
    });

    return created;
  }

  return {
    async start(input: { userId: string }) {
      const user = await prisma.user.findUnique({
        where: { id: input.userId },
        select: { id: true },
      });

      if (!user) {
        throw new NotFoundError('User not found');
      }

      const todayStart = dayStartUtc();
      const existing = await prisma.session.findUnique({
        where: {
          userId_sessionDate: {
            userId: input.userId,
            sessionDate: todayStart,
          },
        },
      });

      if (existing) {
        return {
          created: false,
          session: {
            id: existing.id,
            user_id: existing.userId,
            started_at: existing.startedAt,
          },
        };
      }

      const session = await ensureDailySession(input.userId);

      return {
        created: true,
        session: {
          id: session.id,
          user_id: session.userId,
          started_at: session.startedAt,
        },
      };
    },

    async current(input: { userId: string }) {
      const session = await prisma.session.findFirst({
        where: {
          userId: input.userId,
          startedAt: {
            gte: dayStartUtc(),
            lt: dayEndUtc(),
          },
        },
        orderBy: { startedAt: 'asc' },
      });

      if (!session) {
        return { session: null };
      }

      return {
        session: {
          id: session.id,
          user_id: session.userId,
          started_at: session.startedAt,
        },
      };
    },

    async createMatch(input: { userId: string; gameId: string; levelId: string }) {
      const user = await prisma.user.findUnique({
        where: { id: input.userId },
        select: { id: true },
      });
      if (!user) {
        throw new NotFoundError('User not found');
      }

      const game = await prisma.game.findFirst({
        where: { id: input.gameId, isActive: true, isDeleted: false },
        select: { id: true, name: true },
      });
      if (!game) {
        throw new NotFoundError('Game not found');
      }

      const level = await prisma.level.findFirst({
        where: {
          id: input.levelId,
          isActive: true,
          isDeleted: false,
          preset: { isActive: true, isDeleted: false, game: { isActive: true, isDeleted: false } },
        },
        select: {
          id: true,
          config: true,
          preset: {
            select: {
              id: true,
              gameId: true,
            },
          },
        },
      });
      if (!level) {
        throw new NotFoundError('Level not found');
      }

      if (level.preset.gameId !== input.gameId) {
        throw new NotFoundError('Level does not belong to informed game');
      }

      await assertLevelUnlockedForUser(prisma, input.userId, input.levelId);

      const session = await ensureDailySession(input.userId);

      const match = await prisma.match.create({
        data: {
          sessionId: session.id,
          gameId: input.gameId,
          levelId: input.levelId,
          levelConfigSnapshot: toJsonSnapshot(level.config as Prisma.JsonValue),
        },
      });

      const createdMatch = {
        id: match.id,
        session_id: match.sessionId,
        game_id: match.gameId,
        level_id: match.levelId,
        level_config_snapshot: match.levelConfigSnapshot,
        started_at: match.startedAt,
      };

      return {
        created: true,
        match: createdMatch,
      };
    },
  };
}

export type SessionsService = ReturnType<typeof createSessionsService>;
