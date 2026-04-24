import type { FastifyReply, FastifyRequest } from 'fastify';

import { startProgressQuerySchema } from './progress.schema.js';
import type { ProgressService } from './progress.service.js';

export function createProgressController(service: ProgressService) {
  return {
    async start(request: FastifyRequest, reply: FastifyReply) {
      const query = startProgressQuerySchema.parse(request.query);
      const result = await service.start({
        userId: request.user.sub,
        gameId: query.game_id,
        levelsDetail: query.levels_detail,
      });

      return reply.send(result);
    },
  };
}
