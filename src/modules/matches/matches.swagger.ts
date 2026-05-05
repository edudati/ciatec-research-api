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
};
