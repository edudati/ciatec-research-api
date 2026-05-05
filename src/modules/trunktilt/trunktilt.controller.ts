import type { FastifyReply, FastifyRequest } from 'fastify';

import {
  addTrunktiltEventsBodySchema,
  addTrunktiltPoseBodySchema,
  addTrunktiltWorldBodySchema,
  trunktiltMatchParamsSchema,
} from './trunktilt.schema.js';
import type { TrunktiltService } from './trunktilt.service.js';

export function createTrunktiltController(service: TrunktiltService) {
  return {
    async addWorldTelemetry(request: FastifyRequest, reply: FastifyReply) {
      const params = trunktiltMatchParamsSchema.parse(request.params);
      const body = addTrunktiltWorldBodySchema.parse(request.body);

      const result = await service.addWorldTelemetry({
        userId: request.user.sub,
        matchId: params.match_id,
        frames: body.frames,
      });

      return reply.status(202).send(result);
    },

    async addPoseTelemetry(request: FastifyRequest, reply: FastifyReply) {
      const params = trunktiltMatchParamsSchema.parse(request.params);
      const body = addTrunktiltPoseBodySchema.parse(request.body);

      const result = await service.addPoseTelemetry({
        userId: request.user.sub,
        matchId: params.match_id,
        frames: body.frames,
      });

      return reply.status(202).send(result);
    },

    async addEvents(request: FastifyRequest, reply: FastifyReply) {
      const params = trunktiltMatchParamsSchema.parse(request.params);
      const body = addTrunktiltEventsBodySchema.parse(request.body);

      const result = await service.addEvents({
        userId: request.user.sub,
        matchId: params.match_id,
        events: body.events.map((e) => ({
          type: e.type,
          timestamp: e.timestamp,
          data: e.data as Record<string, unknown>,
        })),
      });

      return reply.status(201).send(result);
    },
  };
}
