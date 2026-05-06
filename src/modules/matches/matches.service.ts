import { Prisma, type PrismaClient } from '@prisma/client';

import { applyUserLevelProgressAfterMatchFinish } from '../progress/user-level-progress-helpers.js';
import { AppError } from '../../shared/errors/app-error.js';
import { ConflictError } from '../../shared/errors/conflict-error.js';
import { NotFoundError } from '../../shared/errors/not-found-error.js';

type MatchesServiceDeps = {
  prisma: PrismaClient;
};

type FinishResponseBody = {
  id: string;
  match_id: string;
  score: number;
  duration_ms: number;
  server_duration_ms: number;
  completed: boolean;
  extra: Prisma.JsonValue;
  created_at: Date;
};

type StoredMatchResultRow = {
  id: string;
  matchId: string;
  score: number;
  durationMs: number;
  serverDurationMs: number | null;
  completed: boolean;
  idempotencyKey: string | null;
  createdAt: Date;
};

function isPrismaUniqueViolation(error: unknown): boolean {
  return error instanceof Prisma.PrismaClientKnownRequestError && error.code === 'P2002';
}

/** Merges `extra` with reserved `client_meta` from the finish body (body wins when `clientMeta` is set). */
function buildMatchResultDetailData(
  extra: Record<string, unknown> | undefined,
  clientMeta: Record<string, string> | undefined,
): Record<string, unknown> {
  const data: Record<string, unknown> = { ...(extra ?? {}) };
  if (clientMeta !== undefined) {
    if (Object.keys(clientMeta).length > 0) {
      data.client_meta = clientMeta;
    } else {
      delete data.client_meta;
    }
  }
  return data;
}

function finishPayloadsMatch(
  input: {
    score: number;
    durationMs: number;
    completed: boolean;
    extra?: Record<string, unknown>;
    clientMeta?: Record<string, string>;
  },
  stored: Pick<StoredMatchResultRow, 'score' | 'durationMs' | 'completed'>,
  storedDetail: Prisma.JsonValue,
): boolean {
  if (
    input.score !== stored.score ||
    input.durationMs !== stored.durationMs ||
    input.completed !== stored.completed
  ) {
    return false;
  }
  if (typeof storedDetail !== 'object' || storedDetail === null || Array.isArray(storedDetail)) {
    return false;
  }
  const expected = buildMatchResultDetailData(input.extra, input.clientMeta);
  return JSON.stringify(expected) === JSON.stringify(storedDetail);
}

function resolveServerDurationMs(row: StoredMatchResultRow, matchStartedAt: Date): number {
  if (row.serverDurationMs != null) {
    return row.serverDurationMs;
  }
  return Math.max(0, Math.round(row.createdAt.getTime() - matchStartedAt.getTime()));
}

function toFinishResponse(
  row: StoredMatchResultRow,
  detailData: Prisma.JsonValue,
  matchStartedAt: Date,
): FinishResponseBody {
  return {
    id: row.id,
    match_id: row.matchId,
    score: row.score,
    duration_ms: row.durationMs,
    server_duration_ms: resolveServerDurationMs(row, matchStartedAt),
    completed: row.completed,
    extra: detailData,
    created_at: row.createdAt,
  };
}

export function createMatchesService({ prisma }: MatchesServiceDeps) {
  async function getAuthorizedMatch(userId: string, matchId: string) {
    const match = await prisma.match.findUnique({
      where: { id: matchId },
      select: {
        id: true,
        gameId: true,
        levelId: true,
        startedAt: true,
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
    async getPreset(input: { userId: string; gameId: string }) {
      const [user, game] = await Promise.all([
        prisma.user.findUnique({ where: { id: input.userId }, select: { id: true } }),
        prisma.game.findUnique({ where: { id: input.gameId }, select: { id: true } }),
      ]);

      if (!user) {
        throw new NotFoundError('User not found');
      }
      if (!game) {
        throw new NotFoundError('Game not found');
      }

      const selectUserGame = {
        id: true,
        gameId: true,
        presetId: true,
        currentLevelId: true,
        preset: {
          select: {
            id: true,
            gameId: true,
            name: true,
            description: true,
            isDefault: true,
            levels: {
              orderBy: { order: 'asc' as const },
              select: { id: true, presetId: true, name: true, order: true },
            },
          },
        },
      } as const;

      let userGame = await prisma.userGame.findUnique({
        where: { userId_gameId: { userId: input.userId, gameId: input.gameId } },
        select: selectUserGame,
      });

      if (!userGame) {
        const firstPreset = await prisma.preset.findFirst({
          where: { gameId: input.gameId },
          orderBy: [{ isDefault: 'desc' }, { id: 'asc' }],
          select: {
            id: true,
            levels: { orderBy: { order: 'asc' }, take: 1, select: { id: true } },
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
          select: selectUserGame,
        });
      }

      return {
        user_game_id: userGame.id,
        game_id: userGame.gameId,
        preset: {
          id: userGame.preset.id,
          game_id: userGame.preset.gameId,
          name: userGame.preset.name,
          description: userGame.preset.description,
          is_default: userGame.preset.isDefault,
          levels: userGame.preset.levels.map((l) => ({
            id: l.id,
            preset_id: l.presetId,
            name: l.name,
            order: l.order,
          })),
        },
        current_level_id: userGame.currentLevelId,
      };
    },

    async getLevel(input: { presetId: string; levelId: string }) {
      const level = await prisma.level.findFirst({
        where: { id: input.levelId, presetId: input.presetId },
        select: { id: true, presetId: true, name: true, order: true, config: true },
      });

      if (!level) {
        throw new NotFoundError('Level not found');
      }

      return {
        id: level.id,
        preset_id: level.presetId,
        name: level.name,
        order: level.order,
        config: level.config,
      };
    },

    async finish(input: {
      userId: string;
      matchId: string;
      score: number;
      durationMs: number;
      completed: boolean;
      extra?: Record<string, unknown>;
      clientMeta?: Record<string, string>;
      idempotencyKey?: string;
    }): Promise<{ statusCode: 200 | 201; body: FinishResponseBody }> {
      const match = await getAuthorizedMatch(input.userId, input.matchId);

      const existing = await prisma.matchResult.findUnique({
        where: { matchId: input.matchId },
        select: {
          id: true,
          matchId: true,
          score: true,
          durationMs: true,
          serverDurationMs: true,
          completed: true,
          idempotencyKey: true,
          createdAt: true,
        },
      });

      if (existing) {
        return finishFromExistingResult({
          prisma,
          existing,
          input,
          matchStartedAt: match.startedAt,
        });
      }

      if (input.idempotencyKey) {
        const keyOwner = await prisma.matchResult.findUnique({
          where: { idempotencyKey: input.idempotencyKey },
          select: { matchId: true },
        });
        if (keyOwner && keyOwner.matchId !== input.matchId) {
          throw new ConflictError('Idempotency key already used');
        }
      }

      const serverDurationMs = Math.max(0, Math.round(Date.now() - match.startedAt.getTime()));

      try {
        const result = await prisma.$transaction(async (tx) => {
          const createdResult = await tx.matchResult.create({
            data: {
              matchId: input.matchId,
              score: input.score,
              durationMs: input.durationMs,
              serverDurationMs,
              completed: input.completed,
              idempotencyKey: input.idempotencyKey ?? null,
            },
          });

          const detailData = buildMatchResultDetailData(input.extra, input.clientMeta);
          const createdDetail = await tx.matchResultDetail.create({
            data: {
              matchId: input.matchId,
              data: detailData as Prisma.InputJsonValue,
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

        const row: StoredMatchResultRow = {
          id: result.createdResult.id,
          matchId: result.createdResult.matchId,
          score: result.createdResult.score,
          durationMs: result.createdResult.durationMs,
          serverDurationMs: result.createdResult.serverDurationMs,
          completed: result.createdResult.completed,
          idempotencyKey: result.createdResult.idempotencyKey,
          createdAt: result.createdResult.createdAt,
        };

        return {
          statusCode: 201,
          body: toFinishResponse(row, result.createdDetail.data, match.startedAt),
        };
      } catch (error) {
        if (!isPrismaUniqueViolation(error)) {
          throw error;
        }
        return reconcileFinishAfterUniqueViolation({ prisma, input });
      }
    },
  };
}

async function finishFromExistingResult({
  prisma,
  existing,
  input,
  matchStartedAt,
}: {
  prisma: PrismaClient;
  existing: StoredMatchResultRow;
  matchStartedAt: Date;
  input: {
    score: number;
    durationMs: number;
    completed: boolean;
    extra?: Record<string, unknown>;
    clientMeta?: Record<string, string>;
    idempotencyKey?: string;
  };
}): Promise<{ statusCode: 200 | 201; body: FinishResponseBody }> {
  const detail = await prisma.matchResultDetail.findUnique({
    where: { matchId: existing.matchId },
    select: { data: true },
  });
  const storedDetail = detail?.data ?? {};

  if (!input.idempotencyKey || existing.idempotencyKey !== input.idempotencyKey) {
    throw new ConflictError('Match already finished');
  }

  if (!finishPayloadsMatch(input, existing, storedDetail)) {
    throw new AppError(
      'Idempotency key reused with different payload',
      409,
      'IDEMPOTENCY_MISMATCH',
    );
  }

  return { statusCode: 200, body: toFinishResponse(existing, storedDetail, matchStartedAt) };
}

async function reconcileFinishAfterUniqueViolation({
  prisma,
  input,
}: {
  prisma: PrismaClient;
  input: {
    matchId: string;
    score: number;
    durationMs: number;
    completed: boolean;
    extra?: Record<string, unknown>;
    clientMeta?: Record<string, string>;
    idempotencyKey?: string;
  };
}): Promise<{ statusCode: 200 | 201; body: FinishResponseBody }> {
  const matchRow = await prisma.match.findUnique({
    where: { id: input.matchId },
    select: { startedAt: true },
  });
  if (!matchRow) {
    throw new NotFoundError('Match not found');
  }
  const matchStartedAt = matchRow.startedAt;

  const byMatch = await prisma.matchResult.findUnique({
    where: { matchId: input.matchId },
    select: {
      id: true,
      matchId: true,
      score: true,
      durationMs: true,
      serverDurationMs: true,
      completed: true,
      idempotencyKey: true,
      createdAt: true,
    },
  });

  if (byMatch) {
    return finishFromExistingResult({
      prisma,
      existing: byMatch,
      input,
      matchStartedAt,
    });
  }

  if (input.idempotencyKey) {
    const byKey = await prisma.matchResult.findUnique({
      where: { idempotencyKey: input.idempotencyKey },
      select: {
        id: true,
        matchId: true,
        score: true,
        durationMs: true,
        serverDurationMs: true,
        completed: true,
        idempotencyKey: true,
        createdAt: true,
      },
    });
    if (byKey) {
      if (byKey.matchId !== input.matchId) {
        throw new ConflictError('Idempotency key already used');
      }
      return finishFromExistingResult({
        prisma,
        existing: byKey,
        input,
        matchStartedAt,
      });
    }
  }

  throw new ConflictError('Match already finished');
}

export type MatchesService = ReturnType<typeof createMatchesService>;
