import type { FastifyReply, FastifyRequest } from 'fastify';

import { ValidationError } from '../../shared/errors/validation-error.js';
import {
  finishMatchBodySchema,
  finishMatchParamsSchema,
  getLevelQuerySchema,
  getPresetQuerySchema,
} from './matches.schema.js';
import type { MatchesService } from './matches.service.js';

export function createMatchesController(service: MatchesService) {
  return {
    async getPreset(request: FastifyRequest, reply: FastifyReply) {
      const query = getPresetQuerySchema.parse(request.query);
      const result = await service.getPreset({ userId: request.user.sub, gameId: query.game_id });
      return reply.send(result);
    },

    async getLevel(request: FastifyRequest, reply: FastifyReply) {
      const query = getLevelQuerySchema.parse(request.query);
      const result = await service.getLevel({ presetId: query.preset_id, levelId: query.level_id });
      return reply.send(result);
    },

    async finish(request: FastifyRequest, reply: FastifyReply) {
      const params = finishMatchParamsSchema.parse(request.params);
      const body = finishMatchBodySchema.parse(request.body);
      const rawKey = request.headers['idempotency-key'];
      const fromHeader =
        typeof rawKey === 'string' && rawKey.trim().length > 0 ? rawKey.trim() : undefined;
      const fromBody = body.client_request_id;

      if (fromHeader !== undefined && fromBody !== undefined && fromHeader !== fromBody) {
        throw new ValidationError('Idempotency-Key and client_request_id must match when both are sent');
      }

      const idempotencyKey = fromHeader ?? fromBody;
      if (idempotencyKey !== undefined && idempotencyKey.length > 128) {
        throw new ValidationError('Idempotency-Key too long');
      }

      const { statusCode, body: payload } = await service.finish({
        userId: request.user.sub,
        matchId: params.match_id,
        score: body.score,
        durationMs: body.duration_ms,
        completed: body.completed,
        extra: body.extra,
        clientMeta: body.client_meta,
        idempotencyKey,
      });

      return reply.status(statusCode).send(payload);
    },
  };
}
