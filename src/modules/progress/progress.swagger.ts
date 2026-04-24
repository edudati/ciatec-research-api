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
      'Uses authenticated user from JWT. If no `user_games` row yet: assigns the **default preset** for that game (`isDefault: true` on the preset) and the first level by `order`, then returns that state. If no default exists, uses the first preset by `id`. If a row already exists, returns that progress unchanged. The trail of all levels in the preset is in `levels` (unlocked, completed, bests, is_current; optional `config` on each when levels_detail=full). `current_level` always includes `config` plus `unlocked`, `completed`, `is_current`, `bests`.',
    security: [{ bearerAuth: [] }],
    querystring: {
      type: 'object',
      required: ['game_id'],
      properties: {
        game_id: { type: 'string', format: 'uuid' },
        levels_detail: {
          type: 'string',
          enum: ['summary', 'full'],
          default: 'summary',
          description:
            'summary: levels[] omits per-level `config` (saves bytes). full: every trail item includes `config`. `current_level` always has `config`.',
        },
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
              description: { type: 'string', nullable: true },
            },
            required: ['id', 'name', 'description'],
          },
          current_level: {
            type: 'object',
            properties: {
              id: { type: 'string', format: 'uuid' },
              name: { type: 'string' },
              order: { type: 'integer' },
              config: { type: 'object' },
              unlocked: { type: 'boolean' },
              completed: { type: 'boolean' },
              is_current: { type: 'boolean' },
              bests: { type: 'object' },
            },
            required: [
              'id',
              'name',
              'order',
              'config',
              'unlocked',
              'completed',
              'is_current',
              'bests',
            ],
          },
          levels: {
            type: 'array',
            items: { type: 'object', additionalProperties: true },
            description: 'All levels in the current preset, ordered, for the trail / map',
          },
        },
        required: ['user_game_id', 'game', 'preset', 'current_level', 'levels'],
      },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      404: { description: 'Related entities not found', ...appError },
    },
  },
};
