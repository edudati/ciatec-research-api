import { Prisma, type PrismaClient } from '@prisma/client';

import { NotFoundError } from '../../shared/errors/not-found-error.js';

type SessionsServiceDeps = {
  prisma: PrismaClient;
};

const RECENT_MATCH_WINDOW_MS = 5000;
const recentMatchByKey = new Map<
  string,
  {
    match: {
      id: string;
      session_id: string;
      game_id: string;
      level_id: string;
      level_config_snapshot: Prisma.JsonValue | null;
      started_at: Date;
    };
    expiresAt: number;
  }
>();

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
      const dedupeKey = `${input.userId}:${input.gameId}:${input.levelId}`;
      const now = Date.now();
      const recent = recentMatchByKey.get(dedupeKey);
      if (recent && recent.expiresAt > now) {
        return {
          created: false,
          match: recent.match,
        };
      }

      const user = await prisma.user.findUnique({
        where: { id: input.userId },
        select: { id: true },
      });
      if (!user) {
        throw new NotFoundError('User not found');
      }

      const game = await prisma.game.findUnique({
        where: { id: input.gameId },
        select: { id: true, name: true },
      });
      if (!game) {
        throw new NotFoundError('Game not found');
      }

      const level = await prisma.level.findUnique({
        where: { id: input.levelId },
        include: {
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

      const session = await ensureDailySession(input.userId);

      const recentDbMatch = await prisma.match.findFirst({
        where: {
          sessionId: session.id,
          gameId: input.gameId,
          levelId: input.levelId,
          startedAt: {
            gte: new Date(now - RECENT_MATCH_WINDOW_MS),
          },
        },
        orderBy: { startedAt: 'desc' },
      });
      if (recentDbMatch) {
        const reusedMatch = {
          id: recentDbMatch.id,
          session_id: recentDbMatch.sessionId,
          game_id: recentDbMatch.gameId,
          level_id: recentDbMatch.levelId,
          level_config_snapshot: recentDbMatch.levelConfigSnapshot,
          started_at: recentDbMatch.startedAt,
        };
        recentMatchByKey.set(dedupeKey, {
          match: reusedMatch,
          expiresAt: now + RECENT_MATCH_WINDOW_MS,
        });
        return {
          created: false,
          match: reusedMatch,
        };
      }

      const match = await prisma.match.create({
        data: {
          sessionId: session.id,
          gameId: input.gameId,
          levelId: input.levelId,
          levelConfigSnapshot: level.config === null ? Prisma.JsonNull : level.config,
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
      recentMatchByKey.set(dedupeKey, {
        match: createdMatch,
        expiresAt: now + RECENT_MATCH_WINDOW_MS,
      });

      return {
        created: true,
        match: createdMatch,
      };
    },
  };
}

export type SessionsService = ReturnType<typeof createSessionsService>;
