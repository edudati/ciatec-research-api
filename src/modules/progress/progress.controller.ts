import type { FastifyReply, FastifyRequest } from 'fastify';

import { levelParamsSchema, presetQuerySchema } from './progress.schema.js';
import type { ProgressService } from './progress.service.js';

export function createProgressController(service: ProgressService) {
  return {
    async getPreset(request: FastifyRequest, reply: FastifyReply) {
      const query = presetQuerySchema.parse(request.query);
      const result = await service.getPreset({
        userId: request.user.sub,
        gameId: query.game_id,
      });

      return reply.send(result);
    },

    async getLevel(request: FastifyRequest, reply: FastifyReply) {
      const params = levelParamsSchema.parse(request.params);
      const result = await service.getLevel({
        userId: request.user.sub,
        levelId: params.level_id,
      });

      return reply.send(result);
    },
  };
}
