import type { FastifyInstance } from 'fastify';

import { prisma } from '../../lib/prisma.js';
import { authenticate } from '../../shared/middlewares/authenticate.js';
import { createUsersController } from './users.controller.js';
import { createUsersService } from './users.service.js';
import { usersSwagger } from './users.swagger.js';

export async function usersRoutes(fastify: FastifyInstance): Promise<void> {
  const service = createUsersService({ prisma });
  const controller = createUsersController(service);

  // TODO: add requireRole('ADMIN', ...) when product locks this surface by role.
  const auth = [authenticate];

  fastify.get('/', { preHandler: auth, schema: usersSwagger.listUsers }, controller.listUsers);
  fastify.get('/:id', { preHandler: auth, schema: usersSwagger.getUser }, controller.getUser);
  fastify.post('/', { preHandler: auth, schema: usersSwagger.createUser }, controller.createUser);
  fastify.patch('/:id', { preHandler: auth, schema: usersSwagger.updateUser }, controller.updateUser);
  fastify.delete('/:id', { preHandler: auth, schema: usersSwagger.deleteUser }, controller.deleteUser);
}
