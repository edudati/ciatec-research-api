import { Prisma, type PrismaClient } from '@prisma/client';

import { ForbiddenError } from '../../shared/errors/forbidden-error.js';
import { NotFoundError } from '../../shared/errors/not-found-error.js';

export type IsolatedBatchGame = 'bubbles' | 'bestbeat';

type MatchBatchIngestDeps = {
  prisma: PrismaClient;
  expectedGameId: string;
  game: IsolatedBatchGame;
};

export function createMatchBatchIngestService({
  prisma,
  expectedGameId,
  game,
}: MatchBatchIngestDeps) {
  async function assertAuthorizedGameMatch(userId: string, matchId: string) {
    const match = await prisma.match.findUnique({
      where: { id: matchId },
      select: {
        id: true,
        gameId: true,
        session: { select: { userId: true } },
      },
    });

    if (!match || match.session.userId !== userId) {
      throw new NotFoundError('Match not found');
    }
    if (match.gameId !== expectedGameId) {
      throw new ForbiddenError('Match does not belong to this game');
    }

    return match;
  }

  return {
    async addEvents(input: {
      userId: string;
      matchId: string;
      events: Array<{
        type: string;
        timestamp: number;
        data: Record<string, unknown>;
      }>;
    }) {
      await assertAuthorizedGameMatch(input.userId, input.matchId);

      const payload = input.events.map((event) => ({
        matchId: input.matchId,
        type: event.type,
        timestamp: BigInt(event.timestamp),
        data: event.data as Prisma.InputJsonValue,
      }));

      const created =
        game === 'bubbles'
          ? await prisma.bubblesEvent.createMany({ data: payload })
          : await prisma.bestbeatEvent.createMany({ data: payload });

      return {
        match_id: input.matchId,
        events_received: input.events.length,
        events_created: created.count,
      };
    },

    async addTelemetryLandmarks(input: {
      userId: string;
      matchId: string;
      frames: Array<{
        timestamp: number;
        data: Record<string, unknown>;
      }>;
    }) {
      await assertAuthorizedGameMatch(input.userId, input.matchId);

      const payload = input.frames.map((frame) => ({
        matchId: input.matchId,
        timestamp: BigInt(frame.timestamp),
        data: frame.data as Prisma.InputJsonValue,
      }));

      const created =
        game === 'bubbles'
          ? await prisma.bubblesLandmark.createMany({ data: payload })
          : await prisma.bestbeatLandmark.createMany({ data: payload });

      return {
        match_id: input.matchId,
        frames_received: input.frames.length,
        frames_created: created.count,
      };
    },

    async addTelemetryWorld(input: {
      userId: string;
      matchId: string;
      frames: Array<{
        timestamp: number;
        device: string;
        data: Record<string, unknown>;
      }>;
    }) {
      await assertAuthorizedGameMatch(input.userId, input.matchId);

      const payload = input.frames.map((frame) => ({
        matchId: input.matchId,
        timestamp: BigInt(frame.timestamp),
        device: frame.device,
        data: frame.data as Prisma.InputJsonValue,
      }));

      const created =
        game === 'bubbles'
          ? await prisma.bubblesWorld.createMany({ data: payload })
          : await prisma.bestbeatWorld.createMany({ data: payload });

      return {
        match_id: input.matchId,
        frames_received: input.frames.length,
        frames_created: created.count,
      };
    },
  };
}

export type MatchBatchIngestService = ReturnType<typeof createMatchBatchIngestService>;
