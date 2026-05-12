import type { FastifySchema } from 'fastify';

const appError = {
  type: 'object',
  properties: {
    success: { type: 'boolean', enum: [false] },
    code: { type: 'string' },
    message: { type: 'string' },
  },
  required: ['success', 'code', 'message'],
} as const;

const zodValidationError = {
  type: 'object',
  properties: {
    success: { type: 'boolean', enum: [false] },
    code: { type: 'string', enum: ['VALIDATION_ERROR'] },
    message: { type: 'string' },
    details: { type: 'array' },
    issues: { type: 'array' },
  },
  required: ['success', 'code', 'message', 'details', 'issues'],
} as const;

export function buildGameBatchSwagger(gameTag: string): Record<string, FastifySchema> {
  return {
    addEvents: {
      tags: [gameTag],
      summary: 'Add match events batch',
      description:
        'Stores a batch of gameplay events for one match in this game’s isolated events table. Match must belong to this game. Up to 500 events per request.',
      security: [{ bearerAuth: [] }],
      params: {
        type: 'object',
        required: ['match_id'],
        properties: {
          match_id: { type: 'string', format: 'uuid' },
        },
      },
      body: {
        type: 'object',
        required: ['events'],
        properties: {
          events: {
            type: 'array',
            minItems: 1,
            maxItems: 500,
            items: {
              type: 'object',
              required: ['type', 'timestamp', 'data'],
              properties: {
                type: { type: 'string' },
                timestamp: { type: 'integer', description: 'Unix epoch em milissegundos' },
                data: { type: 'object', additionalProperties: true },
              },
            },
          },
        },
      },
      response: {
        201: {
          description: 'Events created',
          type: 'object',
          properties: {
            match_id: { type: 'string', format: 'uuid' },
            events_received: { type: 'integer' },
            events_created: { type: 'integer' },
          },
          required: ['match_id', 'events_received', 'events_created'],
        },
        400: { description: 'Validation (Zod)', ...zodValidationError },
        401: { description: 'Unauthorized', ...appError },
        403: { description: 'Match belongs to another game', ...appError },
        404: { description: 'Match not found', ...appError },
      },
    },
    addPoseTelemetry: {
      tags: [gameTag],
      summary: `${gameTag} pose telemetry batch`,
      description:
        'Stores per-frame pose-style samples (e.g. MediaPipe landmarks in `data`). Same path pattern as TrunkTilt `telemetry/pose`. Up to 100 frames per request.',
      security: [{ bearerAuth: [] }],
      params: {
        type: 'object',
        required: ['match_id'],
        properties: {
          match_id: { type: 'string', format: 'uuid' },
        },
      },
      body: {
        type: 'object',
        required: ['frames'],
        properties: {
          frames: {
            type: 'array',
            minItems: 1,
            maxItems: 100,
            items: {
              type: 'object',
              required: ['timestamp', 'data'],
              properties: {
                timestamp: { type: 'integer', description: 'Unix epoch em milissegundos' },
                data: { type: 'object', additionalProperties: true },
              },
            },
          },
        },
      },
      response: {
        201: {
          description: 'Pose frames created',
          type: 'object',
          properties: {
            match_id: { type: 'string', format: 'uuid' },
            frames_received: { type: 'integer' },
            frames_created: { type: 'integer' },
          },
          required: ['match_id', 'frames_received', 'frames_created'],
        },
        400: { description: 'Validation (Zod)', ...zodValidationError },
        401: { description: 'Unauthorized', ...appError },
        403: { description: 'Match belongs to another game', ...appError },
        404: { description: 'Match not found', ...appError },
      },
    },
    addWorldTelemetry: {
      tags: [gameTag],
      summary: `${gameTag} world telemetry batch`,
      description:
        'Stores world / device-attributed telemetry frames. Same path pattern as TrunkTilt `telemetry/world`. Up to 100 frames per request.',
      security: [{ bearerAuth: [] }],
      params: {
        type: 'object',
        required: ['match_id'],
        properties: {
          match_id: { type: 'string', format: 'uuid' },
        },
      },
      body: {
        type: 'object',
        required: ['frames'],
        properties: {
          frames: {
            type: 'array',
            minItems: 1,
            maxItems: 100,
            items: {
              type: 'object',
              required: ['timestamp', 'device', 'data'],
              properties: {
                timestamp: { type: 'integer', description: 'Unix epoch em milissegundos' },
                device: { type: 'string' },
                data: { type: 'object', additionalProperties: true },
              },
            },
          },
        },
      },
      response: {
        201: {
          description: 'World frames created',
          type: 'object',
          properties: {
            match_id: { type: 'string', format: 'uuid' },
            frames_received: { type: 'integer' },
            frames_created: { type: 'integer' },
          },
          required: ['match_id', 'frames_received', 'frames_created'],
        },
        400: { description: 'Validation (Zod)', ...zodValidationError },
        401: { description: 'Unauthorized', ...appError },
        403: { description: 'Match belongs to another game', ...appError },
        404: { description: 'Match not found', ...appError },
      },
    },
  };
}
