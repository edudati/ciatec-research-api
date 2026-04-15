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

export const progressSwagger: Record<string, FastifySchema> = {
  start: {
    tags: ['Progress'],
    summary: 'Start game progress',
    description:
      'Uses authenticated user from JWT. Returns existing user-game progress or creates one with first preset and first level.',
    security: [{ bearerAuth: [] }],
    querystring: {
      type: 'object',
      required: ['game_id'],
      properties: {
        game_id: { type: 'string', format: 'uuid' },
      },
    },
    response: {
      200: {
        description: 'Progress started',
        type: 'object',
        properties: {
          user_game_id: { type: 'string', format: 'uuid' },
          game: {
            type: 'object',
            properties: {
              id: { type: 'string', format: 'uuid' },
              name: { type: 'string' },
            },
            required: ['id', 'name'],
          },
          preset: {
            type: 'object',
            properties: {
              id: { type: 'string', format: 'uuid' },
              name: { type: 'string' },
            },
            required: ['id', 'name'],
          },
          current_level: {
            type: 'object',
            properties: {
              id: { type: 'string', format: 'uuid' },
              name: { type: 'string' },
              order: { type: 'integer' },
              config: { type: 'object' },
            },
            required: ['id', 'name', 'order', 'config'],
          },
        },
        required: ['user_game_id', 'game', 'preset', 'current_level'],
      },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      404: { description: 'Related entities not found', ...appError },
    },
  },
};
