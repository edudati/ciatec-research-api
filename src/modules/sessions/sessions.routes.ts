import type { FastifyInstance } from 'fastify';

import { prisma } from '../../lib/prisma.js';
import { authenticate } from '../../shared/middlewares/authenticate.js';
import { createSessionsController } from './sessions.controller.js';
import { createSessionsService } from './sessions.service.js';
import { sessionsSwagger } from './sessions.swagger.js';

export async function sessionsRoutes(fastify: FastifyInstance): Promise<void> {
  const service = createSessionsService({ prisma });
  const controller = createSessionsController(service);

  fastify.post('/start', { preHandler: [authenticate], schema: sessionsSwagger.start }, controller.start);
  fastify.get('/current', { preHandler: [authenticate], schema: sessionsSwagger.current }, controller.current);
  fastify.post('/matches', { preHandler: [authenticate], schema: sessionsSwagger.createMatch }, controller.createMatch);
}
