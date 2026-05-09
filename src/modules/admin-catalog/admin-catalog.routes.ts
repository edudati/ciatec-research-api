import type { FastifyInstance } from 'fastify';

import { prisma } from '../../lib/prisma.js';
import { authenticate } from '../../shared/middlewares/authenticate.js';
import { requireRole } from '../../shared/middlewares/requireRole.js';
import { createAdminCatalogController } from './admin-catalog.controller.js';
import { createAdminCatalogService } from './admin-catalog.service.js';
import { adminCatalogSwagger } from './admin-catalog.swagger.js';

export async function adminCatalogRoutes(fastify: FastifyInstance): Promise<void> {
  const service = createAdminCatalogService({ prisma });
  const controller = createAdminCatalogController(service);

  const adminOnly = [authenticate, requireRole('ADMIN')];

  // Read endpoints: admin (include inactive and soft-deleted)
  fastify.get('/games', { preHandler: adminOnly, schema: adminCatalogSwagger.listGames }, controller.listGames);
  fastify.get('/games/:game_id', { preHandler: adminOnly, schema: adminCatalogSwagger.getGame }, controller.getGame);
  fastify.get(
    '/games/:game_id/presets',
    { preHandler: adminOnly, schema: adminCatalogSwagger.listPresets },
    controller.listPresets,
  );
  fastify.get('/presets/:preset_id', { preHandler: adminOnly, schema: adminCatalogSwagger.getPreset }, controller.getPreset);
  fastify.get(
    '/presets/:preset_id/levels',
    { preHandler: adminOnly, schema: adminCatalogSwagger.listLevels },
    controller.listLevels,
  );
  fastify.get('/levels/:level_id', { preHandler: adminOnly, schema: adminCatalogSwagger.getLevel }, controller.getLevel);

  // Write endpoints: admin CRUD (no active-only filter; reads/writes by id include soft-deleted rows)
  fastify.post('/games', { preHandler: adminOnly, schema: adminCatalogSwagger.createGame }, controller.createGame);
  fastify.patch('/games/:game_id', { preHandler: adminOnly, schema: adminCatalogSwagger.updateGame }, controller.updateGame);
  fastify.delete('/games/:game_id', { preHandler: adminOnly, schema: adminCatalogSwagger.deleteGame }, controller.deleteGame);

  fastify.post('/presets', { preHandler: adminOnly, schema: adminCatalogSwagger.createPreset }, controller.createPreset);
  fastify.patch(
    '/presets/:preset_id',
    { preHandler: adminOnly, schema: adminCatalogSwagger.updatePreset },
    controller.updatePreset,
  );
  fastify.delete(
    '/presets/:preset_id',
    { preHandler: adminOnly, schema: adminCatalogSwagger.deletePreset },
    controller.deletePreset,
  );

  fastify.post('/levels', { preHandler: adminOnly, schema: adminCatalogSwagger.createLevel }, controller.createLevel);
  fastify.patch(
    '/levels/:level_id',
    { preHandler: adminOnly, schema: adminCatalogSwagger.updateLevel },
    controller.updateLevel,
  );
  fastify.delete(
    '/levels/:level_id',
    { preHandler: adminOnly, schema: adminCatalogSwagger.deleteLevel },
    controller.deleteLevel,
  );
}

