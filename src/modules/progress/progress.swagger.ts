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

const trailLevelItem = {
  type: 'object',
  properties: {
    id: { type: 'string', format: 'uuid' },
    name: { type: 'string' },
    order: { type: 'integer', description: 'Display order on the map (ascending).' },
    unlocked: { type: 'boolean' },
    completed: { type: 'boolean' },
    is_current: { type: 'boolean' },
    bests: { type: 'object' },
  },
  required: ['id', 'name', 'order', 'unlocked', 'completed', 'is_current', 'bests'],
} as const;

export const progressSwagger: Record<string, FastifySchema> = {
  preset: {
    tags: ['Progress'],
    summary: 'Get preset and level trail for a game',
    description:
      'Authenticated user from JWT. Ensures a `user_games` row exists (default preset for the game, first level by `order` if new). Returns preset metadata and **all levels** ordered by `order` for the UI trail. Does **not** include `config`; call `GET /levels/:level_id` to load a phase.',
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
        description: 'Preset and trail',
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
          current_level: trailLevelItem,
          levels: {
            type: 'array',
            items: trailLevelItem,
            description: 'All levels in the user preset, sorted by `order` ascending',
          },
        },
        required: ['user_game_id', 'game', 'preset', 'current_level', 'levels'],
      },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      404: { description: 'Related entities not found', ...appError },
    },
  },
  getLevel: {
    tags: ['Progress'],
    summary: 'Get full level (config) for the authenticated user',
    description:
      'JWT identifies the user. The level must belong to the same preset as `user_games` for that game and must be **unlocked** (403 otherwise). Returns full `config` for loading the phase.',
    security: [{ bearerAuth: [] }],
    params: {
      type: 'object',
      required: ['level_id'],
      properties: {
        level_id: { type: 'string', format: 'uuid' },
      },
    },
    response: {
      200: {
        description: 'Level with config',
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
          preset_id: { type: 'string', format: 'uuid' },
          game_id: { type: 'string', format: 'uuid' },
          name: { type: 'string' },
          order: { type: 'integer' },
          config: { type: 'object', additionalProperties: true },
          unlocked: { type: 'boolean' },
          completed: { type: 'boolean' },
          bests: { type: 'object' },
        },
        required: [
          'id',
          'preset_id',
          'game_id',
          'name',
          'order',
          'config',
          'unlocked',
          'completed',
          'bests',
        ],
      },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Level locked', ...appError },
      404: { description: 'Level or game not found', ...appError },
    },
  },
};
