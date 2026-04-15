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

export const matchesSwagger: Record<string, FastifySchema> = {
  finish: {
    tags: ['Matches'],
    summary: 'Finish match',
    description:
      'Finalizes one match for authenticated user, stores base result and one result detail. Second finish attempt returns conflict.',
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
      required: ['score', 'duration_ms', 'completed'],
      properties: {
        score: { type: 'integer', minimum: 0 },
        duration_ms: { type: 'integer', minimum: 1 },
        completed: { type: 'boolean' },
        extra: { type: 'object', additionalProperties: true },
      },
    },
    response: {
      201: {
        description: 'Match finished',
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
          match_id: { type: 'string', format: 'uuid' },
          score: { type: 'integer' },
          duration_ms: { type: 'integer' },
          completed: { type: 'boolean' },
          extra: { type: 'object', additionalProperties: true },
          created_at: { type: 'string', format: 'date-time' },
        },
        required: ['id', 'match_id', 'score', 'duration_ms', 'completed', 'extra', 'created_at'],
      },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      404: { description: 'Match not found', ...appError },
      409: { description: 'Match already finished', ...appError },
    },
  },
  addEvents: {
    tags: ['Matches'],
    summary: 'Add match events batch',
    description:
      'Stores a batch of events for one match owned by authenticated user. Batch supports up to 500 events per request.',
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
              timestamp: { type: 'string', format: 'date-time' },
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
      404: { description: 'Match not found', ...appError },
    },
  },
  addTelemetryLandmarks: {
    tags: ['Matches'],
    summary: 'Add telemetry landmarks batch',
    description:
      'Stores landmarks frames for one match owned by authenticated user. Batch supports up to 100 frames per request.',
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
              timestamp: { type: 'string', format: 'date-time' },
              data: { type: 'object', additionalProperties: true },
            },
          },
        },
      },
    },
    response: {
      201: {
        description: 'Landmarks created',
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
      404: { description: 'Match not found', ...appError },
    },
  },
  addTelemetryInput: {
    tags: ['Matches'],
    summary: 'Add telemetry input batch',
    description:
      'Stores input telemetry for one match owned by authenticated user. Batch supports up to 100 input items per request.',
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
      required: ['inputs'],
      properties: {
        inputs: {
          type: 'array',
          minItems: 1,
          maxItems: 100,
          items: {
            type: 'object',
            required: ['timestamp', 'device', 'data'],
            properties: {
              timestamp: { type: 'string', format: 'date-time' },
              device: { type: 'string' },
              data: { type: 'object', additionalProperties: true },
            },
          },
        },
      },
    },
    response: {
      201: {
        description: 'Inputs created',
        type: 'object',
        properties: {
          match_id: { type: 'string', format: 'uuid' },
          inputs_received: { type: 'integer' },
          inputs_created: { type: 'integer' },
        },
        required: ['match_id', 'inputs_received', 'inputs_created'],
      },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      404: { description: 'Match not found', ...appError },
    },
  },
};
