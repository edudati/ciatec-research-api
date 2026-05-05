import { Prisma, type PrismaClient } from '@prisma/client';

import { TRUNCKTILT_GAME_ID } from '../../constants/game-ids.js';
import { ConflictError } from '../../shared/errors/conflict-error.js';
import { ForbiddenError } from '../../shared/errors/forbidden-error.js';
import { NotFoundError } from '../../shared/errors/not-found-error.js';

type TrunktiltServiceDeps = {
  prisma: PrismaClient;
};

export function createTrunktiltService({ prisma }: TrunktiltServiceDeps) {
  async function assertTrunktiltMatchOpen(userId: string, matchId: string) {
    const match = await prisma.match.findUnique({
      where: { id: matchId },
      select: {
        id: true,
        gameId: true,
        session: { select: { userId: true } },
        result: { select: { id: true } },
      },
    });

    if (!match || match.session.userId !== userId) {
      throw new NotFoundError('Match not found');
    }
    if (match.gameId !== TRUNCKTILT_GAME_ID) {
      throw new ForbiddenError('Match is not a TrunkTilt match');
    }
    if (match.result) {
      throw new ConflictError('Match already finished');
    }
  }

  return {
    async addWorldTelemetry(input: {
      userId: string;
      matchId: string;
      frames: Array<{
        timestampMs: number;
        frameId: number;
        ballPosition: { x: number; y: number; z: number };
        ballVelocity: { x: number; y: number; z: number };
        velocityMagnitude: number;
        accelerationMagnitude: number;
        planeTiltX: { x: number; y: number; z: number };
        planeTiltZ: { x: number; y: number; z: number };
        inputVirtualX: number;
        inputVirtualZ: number;
      }>;
    }) {
      await assertTrunktiltMatchOpen(input.userId, input.matchId);

      const rows = input.frames.map((f) => ({
        matchId: input.matchId,
        timestampMs: BigInt(f.timestampMs),
        frameId: f.frameId,
        ballPosX: f.ballPosition.x,
        ballPosY: f.ballPosition.y,
        ballPosZ: f.ballPosition.z,
        ballVelX: f.ballVelocity.x,
        ballVelY: f.ballVelocity.y,
        ballVelZ: f.ballVelocity.z,
        velocityMag: f.velocityMagnitude,
        accelMag: f.accelerationMagnitude,
        tiltXX: f.planeTiltX.x,
        tiltXY: f.planeTiltX.y,
        tiltXZ: f.planeTiltX.z,
        tiltZX: f.planeTiltZ.x,
        tiltZY: f.planeTiltZ.y,
        tiltZZ: f.planeTiltZ.z,
        inputVirtX: f.inputVirtualX,
        inputVirtZ: f.inputVirtualZ,
      }));

      const created = await prisma.trunktiltWorld.createMany({
        data: rows,
        skipDuplicates: true,
      });

      return {
        match_id: input.matchId,
        frames_received: input.frames.length,
        rows_inserted: created.count,
      };
    },

    async addPoseTelemetry(input: {
      userId: string;
      matchId: string;
      frames: Array<{
        timestampMs: number;
        frameId: number;
        landmarks: Array<{
          id: number;
          x: number;
          y: number;
          z: number;
          visibility?: number | null;
        }>;
      }>;
    }) {
      await assertTrunktiltMatchOpen(input.userId, input.matchId);

      type PoseRow = {
        matchId: string;
        timestampMs: bigint;
        frameId: number;
        landmarkId: number;
        x: number;
        y: number;
        z: number;
        visibility: number | null;
      };
      const rows: PoseRow[] = [];
      for (const frame of input.frames) {
        for (const lm of frame.landmarks) {
          rows.push({
            matchId: input.matchId,
            timestampMs: BigInt(frame.timestampMs),
            frameId: frame.frameId,
            landmarkId: lm.id,
            x: lm.x,
            y: lm.y,
            z: lm.z,
            visibility: lm.visibility ?? null,
          });
        }
      }

      const created = await prisma.trunktiltPose.createMany({
        data: rows,
        skipDuplicates: true,
      });

      return {
        match_id: input.matchId,
        frames_received: input.frames.length,
        rows_inserted: created.count,
      };
    },

    async addEvents(input: {
      userId: string;
      matchId: string;
      events: Array<{
        type: string;
        timestamp: number;
        data: Record<string, unknown>;
      }>;
    }) {
      await assertTrunktiltMatchOpen(input.userId, input.matchId);

      const payload = input.events.map((event) => ({
        matchId: input.matchId,
        type: event.type,
        timestamp: BigInt(event.timestamp),
        data: event.data as Prisma.InputJsonValue,
      }));

      const created = await prisma.trunktiltEvent.createMany({
        data: payload,
      });

      return {
        match_id: input.matchId,
        events_received: input.events.length,
        events_created: created.count,
      };
    },
  };
}

export type TrunktiltService = ReturnType<typeof createTrunktiltService>;
