import type { FastifyReply, FastifyRequest } from 'fastify';

import {
  loginBodySchema,
  logoutBodySchema,
  refreshBodySchema,
  registerBodySchema,
} from './auth.schema.js';
import type { AuthService } from './auth.service.js';

export function createAuthController(service: AuthService) {
  return {
    async register(request: FastifyRequest, reply: FastifyReply) {
      const body = registerBodySchema.parse(request.body);
      const result = await service.register(body);
      return reply.status(201).send(result);
    },

    async login(request: FastifyRequest, reply: FastifyReply) {
      const body = loginBodySchema.parse(request.body);
      const result = await service.login(body);
      return reply.send(result);
    },

    async refresh(request: FastifyRequest, reply: FastifyReply) {
      const body = refreshBodySchema.parse(request.body);
      const result = await service.refresh(body);
      return reply.send(result);
    },

    async logout(request: FastifyRequest, reply: FastifyReply) {
      const body = logoutBodySchema.parse(request.body ?? {});
      const userId = request.user.sub;
      await service.logout(userId, body.refreshToken);
      return reply.code(204).send();
    },

    async me(request: FastifyRequest, reply: FastifyReply) {
      const userId = request.user.sub;
      const result = await service.me(userId);
      return reply.send(result);
    },
  };
}
