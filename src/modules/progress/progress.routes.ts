import type { FastifyInstance } from 'fastify';

import { prisma } from '../../lib/prisma.js';
import { authenticate } from '../../shared/middlewares/authenticate.js';
import { createProgressController } from './progress.controller.js';
import { createProgressService } from './progress.service.js';
import { progressSwagger } from './progress.swagger.js';

export async function progressRoutes(fastify: FastifyInstance): Promise<void> {
  const service = createProgressService({ prisma });
  const controller = createProgressController(service);

  fastify.get('/preset', { preHandler: [authenticate], schema: progressSwagger.preset }, controller.getPreset);
  fastify.get(
    '/levels/:level_id',
    { preHandler: [authenticate], schema: progressSwagger.getLevel },
    controller.getLevel,
  );
}
