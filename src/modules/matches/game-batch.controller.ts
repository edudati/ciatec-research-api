import type { FastifyReply, FastifyRequest } from 'fastify';

import {
  addMatchEventsBodySchema,
  addPoseTelemetryBodySchema,
  addWorldTelemetryBodySchema,
  finishMatchParamsSchema,
} from './matches.schema.js';
import type { MatchBatchIngestService } from './match-batch-ingest.service.js';

export function createGameBatchController(service: MatchBatchIngestService) {
  return {
    async addEvents(request: FastifyRequest, reply: FastifyReply) {
      const params = finishMatchParamsSchema.parse(request.params);
      const body = addMatchEventsBodySchema.parse(request.body);

      const result = await service.addEvents({
        userId: request.user.sub,
        matchId: params.match_id,
        events: body.events,
      });

      return reply.status(201).send(result);
    },

    async addPoseTelemetry(request: FastifyRequest, reply: FastifyReply) {
      const params = finishMatchParamsSchema.parse(request.params);
      const body = addPoseTelemetryBodySchema.parse(request.body);

      const result = await service.addPoseTelemetry({
        userId: request.user.sub,
        matchId: params.match_id,
        frames: body.frames,
      });

      return reply.status(201).send(result);
    },

    async addWorldTelemetry(request: FastifyRequest, reply: FastifyReply) {
      const params = finishMatchParamsSchema.parse(request.params);
      const body = addWorldTelemetryBodySchema.parse(request.body);

      const result = await service.addWorldTelemetry({
        userId: request.user.sub,
        matchId: params.match_id,
        frames: body.frames,
      });

      return reply.status(201).send(result);
    },
  };
}
