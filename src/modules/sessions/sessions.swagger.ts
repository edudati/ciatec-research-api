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

export const sessionsSwagger: Record<string, FastifySchema> = {
  start: {
    tags: ['Sessions'],
    summary: 'Start daily session',
    description:
      'Creates a session for the authenticated user only if no session exists for today. Otherwise returns current daily session.',
    security: [{ bearerAuth: [] }],
    response: {
      200: {
        description: 'Daily session already exists',
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
          user_id: { type: 'string', format: 'uuid' },
          started_at: { type: 'string', format: 'date-time' },
        },
        required: ['id', 'user_id', 'started_at'],
      },
      201: {
        description: 'Daily session created',
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
          user_id: { type: 'string', format: 'uuid' },
          started_at: { type: 'string', format: 'date-time' },
        },
        required: ['id', 'user_id', 'started_at'],
      },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      404: { description: 'User not found', ...appError },
    },
  },

  current: {
    tags: ['Sessions'],
    summary: 'Get current daily session',
    description: 'Returns today session for authenticated user or null if not created yet.',
    security: [{ bearerAuth: [] }],
    response: {
      200: {
        description: 'Current session lookup',
        type: 'object',
        properties: {
          session: {
            anyOf: [
              {
                type: 'object',
                properties: {
                  id: { type: 'string', format: 'uuid' },
                  user_id: { type: 'string', format: 'uuid' },
                  started_at: { type: 'string', format: 'date-time' },
                },
                required: ['id', 'user_id', 'started_at'],
              },
              { type: 'null' },
            ],
          },
        },
        required: ['session'],
      },
      401: { description: 'Unauthorized', ...appError },
    },
  },

  createMatch: {
    tags: ['Sessions'],
    summary: 'Create match in current daily session',
    description:
      'Creates one match for one game and one level for authenticated user. If daily session does not exist, it is created automatically.',
    security: [{ bearerAuth: [] }],
    body: {
      type: 'object',
      required: ['game_id', 'level_id'],
      properties: {
        game_id: { type: 'string', format: 'uuid' },
        level_id: { type: 'string', format: 'uuid' },
      },
    },
    response: {
      200: {
        description: 'Recent duplicate request reused existing match',
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
          session_id: { type: 'string', format: 'uuid' },
          game_id: { type: 'string', format: 'uuid' },
          level_id: { type: 'string', format: 'uuid' },
          level_config_snapshot: { type: 'object' },
          started_at: { type: 'string', format: 'date-time' },
        },
        required: [
          'id',
          'session_id',
          'game_id',
          'level_id',
          'level_config_snapshot',
          'started_at',
        ],
      },
      201: {
        description: 'Match created',
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
          session_id: { type: 'string', format: 'uuid' },
          game_id: { type: 'string', format: 'uuid' },
          level_id: { type: 'string', format: 'uuid' },
          level_config_snapshot: { type: 'object' },
          started_at: { type: 'string', format: 'date-time' },
        },
        required: [
          'id',
          'session_id',
          'game_id',
          'level_id',
          'level_config_snapshot',
          'started_at',
        ],
      },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Level is locked for this user', ...appError },
      404: { description: 'Related entities not found', ...appError },
    },
  },
};
