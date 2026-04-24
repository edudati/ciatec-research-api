import { Prisma, type PrismaClient } from '@prisma/client';

import { applyUserLevelProgressAfterMatchFinish } from '../progress/user-level-progress-helpers.js';
import { ConflictError } from '../../shared/errors/conflict-error.js';
import { NotFoundError } from '../../shared/errors/not-found-error.js';

type MatchesServiceDeps = {
  prisma: PrismaClient;
};

export function createMatchesService({ prisma }: MatchesServiceDeps) {
  async function getAuthorizedMatch(userId: string, matchId: string) {
    const match = await prisma.match.findUnique({
      where: { id: matchId },
      select: {
        id: true,
        gameId: true,
        levelId: true,
        session: { select: { userId: true } },
        level: { select: { presetId: true, order: true } },
      },
    });

    if (!match || match.session.userId !== userId) {
      throw new NotFoundError('Match not found');
    }

    return match;
  }

  return {
    async finish(
      input: {
        userId: string;
        matchId: string;
        score: number;
        durationMs: number;
        completed: boolean;
        extra?: Record<string, unknown>;
      },
    ) {
      const match = await getAuthorizedMatch(input.userId, input.matchId);

      const existing = await prisma.matchResult.findUnique({
        where: { matchId: input.matchId },
        select: { id: true },
      });
      if (existing) {
        throw new ConflictError('Match already finished');
      }

      const result = await prisma.$transaction(async (tx) => {
        const createdResult = await tx.matchResult.create({
          data: {
            matchId: input.matchId,
            score: input.score,
            durationMs: input.durationMs,
            completed: input.completed,
          },
        });

        const createdDetail = await tx.matchResultDetail.create({
          data: {
            matchId: input.matchId,
            data: (input.extra ?? {}) as Prisma.InputJsonValue,
          },
        });

        await applyUserLevelProgressAfterMatchFinish(tx, {
          userId: input.userId,
          gameId: match.gameId,
          levelId: match.levelId,
          levelPresetId: match.level.presetId,
          levelOrder: match.level.order,
          completed: input.completed,
          score: input.score,
          durationMs: input.durationMs,
          extra: input.extra,
        });

        return { createdResult, createdDetail };
      });

      return {
        id: result.createdResult.id,
        match_id: result.createdResult.matchId,
        score: result.createdResult.score,
        duration_ms: result.createdResult.durationMs,
        completed: result.createdResult.completed,
        extra: result.createdDetail.data,
        created_at: result.createdResult.createdAt,
      };
    },

    async addEvents(
      input: {
        userId: string;
        matchId: string;
        events: Array<{
          type: string;
          timestamp: number;
          data: Record<string, unknown>;
        }>;
      },
    ) {
      await getAuthorizedMatch(input.userId, input.matchId);

      const payload = input.events.map((event) => ({
        matchId: input.matchId,
        type: event.type,
        timestamp: BigInt(event.timestamp),
        data: event.data as Prisma.InputJsonValue,
      }));

      const created = await prisma.matchEvent.createMany({
        data: payload,
      });

      return {
        match_id: input.matchId,
        events_received: input.events.length,
        events_created: created.count,
      };
    },

    async addTelemetryLandmarks(
      input: {
        userId: string;
        matchId: string;
        frames: Array<{
          timestamp: number;
          data: Record<string, unknown>;
        }>;
      },
    ) {
      await getAuthorizedMatch(input.userId, input.matchId);

      const payload = input.frames.map((frame) => ({
        matchId: input.matchId,
        timestamp: BigInt(frame.timestamp),
        data: frame.data as Prisma.InputJsonValue,
      }));

      const created = await prisma.telemetryLandmark.createMany({
        data: payload,
      });

      return {
        match_id: input.matchId,
        frames_received: input.frames.length,
        frames_created: created.count,
      };
    },

    async addTelemetryInput(
      input: {
        userId: string;
        matchId: string;
        inputs: Array<{
          timestamp: number;
          device: string;
          data: Record<string, unknown>;
        }>;
      },
    ) {
      await getAuthorizedMatch(input.userId, input.matchId);

      const payload = input.inputs.map((item) => ({
        matchId: input.matchId,
        timestamp: BigInt(item.timestamp),
        device: item.device,
        data: item.data as Prisma.InputJsonValue,
      }));

      const created = await prisma.telemetryInput.createMany({
        data: payload,
      });

      return {
        match_id: input.matchId,
        inputs_received: input.inputs.length,
        inputs_created: created.count,
      };
    },
  };
}

export type MatchesService = ReturnType<typeof createMatchesService>;
