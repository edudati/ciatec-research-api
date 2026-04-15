import type { FastifyInstance } from 'fastify';

import { prisma } from '../../lib/prisma.js';
import { authenticate } from '../../shared/middlewares/authenticate.js';
import { createMatchesController } from './matches.controller.js';
import { createMatchesService } from './matches.service.js';
import { matchesSwagger } from './matches.swagger.js';

export async function matchesRoutes(fastify: FastifyInstance): Promise<void> {
  const service = createMatchesService({ prisma });
  const controller = createMatchesController(service);

  fastify.post(
    '/:match_id/finish',
    { preHandler: [authenticate], schema: matchesSwagger.finish },
    controller.finish,
  );
  fastify.post(
    '/:match_id/events',
    { preHandler: [authenticate], schema: matchesSwagger.addEvents },
    controller.addEvents,
  );
  fastify.post(
    '/:match_id/telemetry/landmarks',
    { preHandler: [authenticate], schema: matchesSwagger.addTelemetryLandmarks },
    controller.addTelemetryLandmarks,
  );
  fastify.post(
    '/:match_id/telemetry/input',
    { preHandler: [authenticate], schema: matchesSwagger.addTelemetryInput },
    controller.addTelemetryInput,
  );
}
