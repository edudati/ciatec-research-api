import type { FastifyReply, FastifyRequest } from 'fastify';

import { createMatchBodySchema } from './sessions.schema.js';
import type { SessionsService } from './sessions.service.js';

export function createSessionsController(service: SessionsService) {
  return {
    async start(request: FastifyRequest, reply: FastifyReply) {
      const userId = request.user.sub;
      const result = await service.start({ userId });
      return reply.status(result.created ? 201 : 200).send(result.session);
    },

    async current(request: FastifyRequest, reply: FastifyReply) {
      const userId = request.user.sub;
      const result = await service.current({ userId });
      return reply.send(result);
    },

    async createMatch(request: FastifyRequest, reply: FastifyReply) {
      const body = createMatchBodySchema.parse(request.body);
      const result = await service.createMatch({
        userId: request.user.sub,
        gameId: body.game_id,
        levelId: body.level_id,
      });
      return reply.status(201).send(result.match);
    },
  };
}
