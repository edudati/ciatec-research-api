import type { FastifyReply, FastifyRequest } from 'fastify';

import type { UsersService } from './users.service.js';
import {
  createUserBodySchema,
  listUsersQuerySchema,
  patchUserBodySchema,
  userIdParamsSchema,
} from './users.schema.js';

export function createUsersController(service: UsersService) {
  return {
    async listUsers(request: FastifyRequest, reply: FastifyReply) {
      const query = listUsersQuerySchema.parse(request.query);
      const result = await service.listUsers(query);
      return reply.send(result);
    },

    async getUser(request: FastifyRequest, reply: FastifyReply) {
      const params = userIdParamsSchema.parse(request.params);
      const result = await service.getUserById(params.id);
      return reply.send(result);
    },

    async createUser(request: FastifyRequest, reply: FastifyReply) {
      const body = createUserBodySchema.parse(request.body);
      const result = await service.createUser(body);
      return reply.status(201).send(result);
    },

    async updateUser(request: FastifyRequest, reply: FastifyReply) {
      const params = userIdParamsSchema.parse(request.params);
      const body = patchUserBodySchema.parse(request.body);
      const result = await service.updateUser(params.id, body);
      return reply.send(result);
    },

    async deleteUser(request: FastifyRequest, reply: FastifyReply) {
      const params = userIdParamsSchema.parse(request.params);
      await service.softDeleteUser(params.id);
      return reply.status(204).send();
    },
  };
}
