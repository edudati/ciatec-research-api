import type { FastifyReply, FastifyRequest } from 'fastify';

import {
  addMatchEventsBodySchema,
  addTelemetryLandmarksBodySchema,
  addTelemetryWorldBodySchema,
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

    async addTelemetryLandmarks(request: FastifyRequest, reply: FastifyReply) {
      const params = finishMatchParamsSchema.parse(request.params);
      const body = addTelemetryLandmarksBodySchema.parse(request.body);

      const result = await service.addTelemetryLandmarks({
        userId: request.user.sub,
        matchId: params.match_id,
        frames: body.frames,
      });

      return reply.status(201).send(result);
    },

    async addTelemetryWorld(request: FastifyRequest, reply: FastifyReply) {
      const params = finishMatchParamsSchema.parse(request.params);
      const body = addTelemetryWorldBodySchema.parse(request.body);

      const result = await service.addTelemetryWorld({
        userId: request.user.sub,
        matchId: params.match_id,
        frames: body.frames,
      });

      return reply.status(201).send(result);
    },
  };
}
