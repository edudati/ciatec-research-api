import type { FastifyInstance } from 'fastify';

import { prisma } from '../../lib/prisma.js';
import { authenticate } from '../../shared/middlewares/authenticate.js';
import { createTrunktiltController } from './trunktilt.controller.js';
import { createTrunktiltService } from './trunktilt.service.js';
import { trunktiltSwagger } from './trunktilt.swagger.js';

export async function trunktiltRoutes(fastify: FastifyInstance): Promise<void> {
  const service = createTrunktiltService({ prisma });
  const controller = createTrunktiltController(service);

  fastify.post(
    '/matches/:match_id/telemetry/world',
    { preHandler: [authenticate], schema: trunktiltSwagger.addWorldTelemetry },
    controller.addWorldTelemetry,
  );
  fastify.post(
    '/matches/:match_id/telemetry/pose',
    { preHandler: [authenticate], schema: trunktiltSwagger.addPoseTelemetry },
    controller.addPoseTelemetry,
  );
  fastify.post(
    '/matches/:match_id/events',
    { preHandler: [authenticate], schema: trunktiltSwagger.addEvents },
    controller.addEvents,
  );
}
