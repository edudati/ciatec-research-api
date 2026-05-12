import type { FastifyInstance } from 'fastify';

import { BUBBLES_GAME_ID } from '../../constants/game-ids.js';
import { prisma } from '../../lib/prisma.js';
import { authenticate } from '../../shared/middlewares/authenticate.js';
import { createGameBatchController } from '../matches/game-batch.controller.js';
import { buildGameBatchSwagger } from '../matches/game-batch.swagger.js';
import { createMatchBatchIngestService } from '../matches/match-batch-ingest.service.js';

const swagger = buildGameBatchSwagger('Bubbles');

export async function bubblesRoutes(fastify: FastifyInstance): Promise<void> {
  const service = createMatchBatchIngestService({
    prisma,
    expectedGameId: BUBBLES_GAME_ID,
    game: 'bubbles',
  });
  const controller = createGameBatchController(service);

  fastify.post(
    '/matches/:match_id/telemetry/world',
    { preHandler: [authenticate], schema: swagger.addWorldTelemetry },
    controller.addWorldTelemetry,
  );
  fastify.post(
    '/matches/:match_id/telemetry/pose',
    { preHandler: [authenticate], schema: swagger.addPoseTelemetry },
    controller.addPoseTelemetry,
  );
  fastify.post(
    '/matches/:match_id/events',
    { preHandler: [authenticate], schema: swagger.addEvents },
    controller.addEvents,
  );
}
