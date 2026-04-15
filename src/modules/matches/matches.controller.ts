import type { FastifyReply, FastifyRequest } from 'fastify';

import {
  addMatchEventsBodySchema,
  addTelemetryInputBodySchema,
  addTelemetryLandmarksBodySchema,
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

    async addTelemetryInput(request: FastifyRequest, reply: FastifyReply) {
      const params = finishMatchParamsSchema.parse(request.params);
      const body = addTelemetryInputBodySchema.parse(request.body);

      const result = await service.addTelemetryInput({
        userId: request.user.sub,
        matchId: params.match_id,
        inputs: body.inputs,
      });

      return reply.status(201).send(result);
    },
  };
}
