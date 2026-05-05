import type { FastifyInstance } from 'fastify';

import { BESTBEAT_GAME_ID } from '../../constants/game-ids.js';
import { prisma } from '../../lib/prisma.js';
import { authenticate } from '../../shared/middlewares/authenticate.js';
import { createGameBatchController } from '../matches/game-batch.controller.js';
import { buildGameBatchSwagger } from '../matches/game-batch.swagger.js';
import { createMatchBatchIngestService } from '../matches/match-batch-ingest.service.js';

const swagger = buildGameBatchSwagger('Bestbeat');

export async function bestbeatRoutes(fastify: FastifyInstance): Promise<void> {
  const service = createMatchBatchIngestService({
    prisma,
    expectedGameId: BESTBEAT_GAME_ID,
    game: 'bestbeat',
  });
  const controller = createGameBatchController(service);

  fastify.post(
    '/matches/:match_id/events',
    { preHandler: [authenticate], schema: swagger.addEvents },
    controller.addEvents,
  );
  fastify.post(
    '/matches/:match_id/telemetry/landmarks',
    { preHandler: [authenticate], schema: swagger.addTelemetryLandmarks },
    controller.addTelemetryLandmarks,
  );
  fastify.post(
    '/matches/:match_id/telemetry/world',
    { preHandler: [authenticate], schema: swagger.addTelemetryWorld },
    controller.addTelemetryWorld,
  );
}
