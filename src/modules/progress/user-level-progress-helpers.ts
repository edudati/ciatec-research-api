import { Prisma, type PrismaClient } from '@prisma/client';

import { ForbiddenError } from '../../shared/errors/forbidden-error.js';
import { NotFoundError } from '../../shared/errors/not-found-error.js';

import { mergeLevelBests } from './level-bests.js';

export type LevelProgressDb = PrismaClient;

const emptyBests: Prisma.InputJsonValue = {};

/**
 * Unlocks the first level of a preset (linear entry). Idempotent.
 */
export async function ensureFirstLevelUnlockedInPreset(
  db: LevelProgressDb,
  userId: string,
  presetId: string,
) {
  const first = await db.level.findFirst({
    where: { presetId },
    orderBy: { order: 'asc' },
    select: { id: true },
  });
  if (!first) {
    return;
  }
  await db.userLevelProgress.upsert({
    where: { userId_levelId: { userId, levelId: first.id } },
    create: { userId, levelId: first.id, unlocked: true, completed: false, bests: emptyBests },
    update: { unlocked: true },
  });
}

/**
 * Used before creating a match or returning level config: the level must be unlocked, or be the first level in its preset (then we seed and allow).
 */
export async function assertLevelUnlockedForUser(
  db: PrismaClient,
  userId: string,
  levelId: string,
) {
  const level = await db.level.findUnique({
    where: { id: levelId },
    select: { id: true, presetId: true, order: true },
  });
  if (!level) {
    throw new NotFoundError('Level not found');
  }

  const first = await db.level.findFirst({
    where: { presetId: level.presetId },
    orderBy: { order: 'asc' },
    select: { id: true },
  });

  if (first && levelId === first.id) {
    await ensureFirstLevelUnlockedInPreset(db, userId, level.presetId);
    return;
  }

  const row = await db.userLevelProgress.findUnique({
    where: { userId_levelId: { userId, levelId } },
  });
  if (row?.unlocked) {
    return;
  }
  throw new ForbiddenError('Level is locked');
}

type FinishInput = {
  userId: string;
  gameId: string;
  levelId: string;
  levelPresetId: string;
  levelOrder: number;
  completed: boolean;
  score: number;
  durationMs: number;
  extra?: Record<string, unknown>;
};

/**
 * Run inside the same Prisma transaction as match result: merge bests, completed, unlock next on success, and keep user_games in sync.
 */
export async function applyUserLevelProgressAfterMatchFinish(
  tx: Prisma.TransactionClient,
  input: FinishInput,
) {
  const prior = await tx.userLevelProgress.findUnique({
    where: { userId_levelId: { userId: input.userId, levelId: input.levelId } },
  });
  const mergedBests = mergeLevelBests(prior?.bests ?? null, {
    score: input.score,
    durationMs: input.durationMs,
    extra: input.extra,
  });
  const nextCompleted = (prior?.completed ?? false) || input.completed;

  await tx.userLevelProgress.upsert({
    where: { userId_levelId: { userId: input.userId, levelId: input.levelId } },
    create: {
      userId: input.userId,
      levelId: input.levelId,
      unlocked: true,
      completed: nextCompleted,
      bests: mergedBests,
    },
    update: { unlocked: true, completed: nextCompleted, bests: mergedBests },
  });

  if (!input.completed) {
    return;
  }

  const userGame = await tx.userGame.findUnique({
    where: {
      userId_gameId: {
        userId: input.userId,
        gameId: input.gameId,
      },
    },
    select: {
      id: true,
      currentLevelId: true,
    },
  });

  if (!userGame) {
    return;
  }

  if (userGame.currentLevelId !== input.levelId) {
    return;
  }

  const nextLevel = await tx.level.findFirst({
    where: { presetId: input.levelPresetId, order: { gt: input.levelOrder } },
    orderBy: { order: 'asc' },
    select: { id: true },
  });

  if (nextLevel) {
    await tx.userLevelProgress.upsert({
      where: { userId_levelId: { userId: input.userId, levelId: nextLevel.id } },
      create: {
        userId: input.userId,
        levelId: nextLevel.id,
        unlocked: true,
        completed: false,
        bests: emptyBests,
      },
      update: { unlocked: true },
    });
    await tx.userGame.update({
      where: { id: userGame.id },
      data: { currentLevelId: nextLevel.id },
    });
  }
}
