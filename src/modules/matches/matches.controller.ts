import type { FastifyReply, FastifyRequest } from 'fastify';

import {
  finishMatchBodySchema,
  finishMatchParamsSchema,
} from './matches.schema.js';
import type { MatchesService } from './matches.service.js';

export function createMatchesController(service: MatchesService) {
  return {
    async finish(request: FastifyRequest, reply: FastifyReply) {
      const params = finishMatchParamsSchema.parse(request.params);
      const body = finishMatchBodySchema.parse(request.body);

      const result = await service.finish({
        userId: request.user.sub,
        matchId: params.match_id,
        score: body.score,
        durationMs: body.duration_ms,
        completed: body.completed,
        extra: body.extra,
      });

      return reply.status(201).send(result);
    },
  };
}
