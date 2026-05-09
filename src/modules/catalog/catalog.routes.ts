import type { FastifyInstance } from 'fastify';

import { prisma } from '../../lib/prisma.js';
import { authenticate } from '../../shared/middlewares/authenticate.js';
import { requireRole } from '../../shared/middlewares/requireRole.js';
import { createCatalogController } from './catalog.controller.js';
import { createCatalogService } from './catalog.service.js';
import { catalogSwagger } from './catalog.swagger.js';

export async function catalogRoutes(fastify: FastifyInstance): Promise<void> {
  const service = createCatalogService({ prisma });
  const controller = createCatalogController(service);

  // Read endpoints: authenticated (catálogo do servidor / tooling)
  fastify.get('/games', { preHandler: [authenticate], schema: catalogSwagger.listGames }, controller.listGames);
  fastify.get('/games/:game_id', { preHandler: [authenticate], schema: catalogSwagger.getGame }, controller.getGame);
  fastify.get(
    '/games/:game_id/presets',
    { preHandler: [authenticate], schema: catalogSwagger.listPresets },
    controller.listPresets,
  );
  fastify.get('/presets/:preset_id', { preHandler: [authenticate], schema: catalogSwagger.getPreset }, controller.getPreset);
  fastify.get(
    '/presets/:preset_id/levels',
    { preHandler: [authenticate], schema: catalogSwagger.listLevels },
    controller.listLevels,
  );
  fastify.get('/levels/:level_id', { preHandler: [authenticate], schema: catalogSwagger.getLevel }, controller.getLevel);

  // Write endpoints: restricted
  const catalogWrite = [authenticate, requireRole('ADMIN', 'RESEARCHER')];
  fastify.post('/games', { preHandler: catalogWrite, schema: catalogSwagger.createGame }, controller.createGame);
  fastify.patch('/games/:game_id', { preHandler: catalogWrite, schema: catalogSwagger.updateGame }, controller.updateGame);
  fastify.delete('/games/:game_id', { preHandler: catalogWrite, schema: catalogSwagger.deleteGame }, controller.deleteGame);

  fastify.post('/presets', { preHandler: catalogWrite, schema: catalogSwagger.createPreset }, controller.createPreset);
  fastify.patch(
    '/presets/:preset_id',
    { preHandler: catalogWrite, schema: catalogSwagger.updatePreset },
    controller.updatePreset,
  );
  fastify.delete(
    '/presets/:preset_id',
    { preHandler: catalogWrite, schema: catalogSwagger.deletePreset },
    controller.deletePreset,
  );

  fastify.post('/levels', { preHandler: catalogWrite, schema: catalogSwagger.createLevel }, controller.createLevel);
  fastify.patch(
    '/levels/:level_id',
    { preHandler: catalogWrite, schema: catalogSwagger.updateLevel },
    controller.updateLevel,
  );
  fastify.delete(
    '/levels/:level_id',
    { preHandler: catalogWrite, schema: catalogSwagger.deleteLevel },
    controller.deleteLevel,
  );
}

