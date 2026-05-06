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
  getPreset: {
    tags: ['Matches'],
    summary: 'Get preset for game/player',
    description: 'Returns the selected preset for the authenticated user in a given game (creates one if missing).',
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
        description: 'Preset for user in game',
        type: 'object',
        properties: {
          user_game_id: { type: 'string', format: 'uuid' },
          game_id: { type: 'string', format: 'uuid' },
          preset: {
            type: 'object',
            properties: {
              id: { type: 'string', format: 'uuid' },
              game_id: { type: 'string', format: 'uuid' },
              name: { type: 'string' },
              description: { type: ['string', 'null'] },
              is_default: { type: 'boolean' },
              levels: {
                type: 'array',
                items: {
                  type: 'object',
                  properties: {
                    id: { type: 'string', format: 'uuid' },
                    preset_id: { type: 'string', format: 'uuid' },
                    name: { type: 'string' },
                    order: { type: 'integer' },
                  },
                  required: ['id', 'preset_id', 'name', 'order'],
                },
              },
            },
            required: ['id', 'game_id', 'name', 'description', 'is_default', 'levels'],
          },
          current_level_id: { type: 'string', format: 'uuid' },
        },
        required: ['user_game_id', 'game_id', 'preset', 'current_level_id'],
      },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      404: { description: 'Not found', ...appError },
    },
  },

  getLevel: {
    tags: ['Matches'],
    summary: 'Get full level',
    description: 'Returns the full level (including config) for a given preset_id + level_id.',
    security: [{ bearerAuth: [] }],
    querystring: {
      type: 'object',
      required: ['preset_id', 'level_id'],
      properties: {
        preset_id: { type: 'string', format: 'uuid' },
        level_id: { type: 'string', format: 'uuid' },
      },
    },
    response: {
      200: {
        description: 'Level',
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
          preset_id: { type: 'string', format: 'uuid' },
          name: { type: 'string' },
          order: { type: 'integer' },
          config: { type: 'object', additionalProperties: true },
        },
        required: ['id', 'preset_id', 'name', 'order', 'config'],
      },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      404: { description: 'Level not found', ...appError },
    },
  },

  finish: {
    tags: ['Matches'],
    summary: 'Finish match',
    description:
      'Finalizes one match for authenticated user, stores base result and one result detail. Optional client_meta (app/build/platform) is merged into result detail JSON under the key client_meta. For safe retries after timeouts, send the same opaque key on every attempt: header Idempotency-Key and/or body client_request_id (if both are sent they must be equal). Replays with the same key and payload return 200 with the stored result; second finish without a matching key returns conflict.',
    security: [{ bearerAuth: [] }],
    headers: {
      type: 'object',
      properties: {
        'idempotency-key': {
          type: 'string',
          maxLength: 128,
          description: 'Opaque key (e.g. UUID) for safe retries of this finish request.',
        },
      },
    },
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
        client_request_id: {
          type: 'string',
          maxLength: 128,
          description:
            'Optional idempotency token (same as Idempotency-Key header) when headers are inconvenient; must match the header if both are provided.',
        },
        client_meta: {
          type: 'object',
          additionalProperties: false,
          description:
            'Optional client/build metadata; stored inside result detail under client_meta. Unknown properties are rejected.',
          properties: {
            app_version: { type: 'string', maxLength: 128 },
            unity_version: { type: 'string', maxLength: 64 },
            platform: { type: 'string', maxLength: 64 },
            device_model: { type: 'string', maxLength: 128 },
            locale: { type: 'string', maxLength: 32 },
          },
        },
        extra: { type: 'object', additionalProperties: true },
      },
    },
    response: {
      200: {
        description: 'Idempotent replay — match was already finished with this Idempotency-Key and same payload',
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
          match_id: { type: 'string', format: 'uuid' },
          score: { type: 'integer' },
          duration_ms: { type: 'integer' },
          server_duration_ms: {
            type: 'integer',
            minimum: 0,
            description: 'Elapsed time from match start to finish using server clocks (ms).',
          },
          completed: { type: 'boolean' },
          extra: { type: 'object', additionalProperties: true },
          created_at: { type: 'string', format: 'date-time' },
        },
        required: [
          'id',
          'match_id',
          'score',
          'duration_ms',
          'server_duration_ms',
          'completed',
          'extra',
          'created_at',
        ],
      },
      201: {
        description: 'Match finished',
        type: 'object',
        properties: {
          id: { type: 'string', format: 'uuid' },
          match_id: { type: 'string', format: 'uuid' },
          score: { type: 'integer' },
          duration_ms: { type: 'integer' },
          server_duration_ms: {
            type: 'integer',
            minimum: 0,
            description: 'Elapsed time from match start to finish using server clocks (ms).',
          },
          completed: { type: 'boolean' },
          extra: { type: 'object', additionalProperties: true },
          created_at: { type: 'string', format: 'date-time' },
        },
        required: [
          'id',
          'match_id',
          'score',
          'duration_ms',
          'server_duration_ms',
          'completed',
          'extra',
          'created_at',
        ],
      },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      404: { description: 'Match not found', ...appError },
      409: {
        description:
          'Conflict: match already finished, idempotency key reused for another match, or key reused with different payload (code IDEMPOTENCY_MISMATCH)',
        ...appError,
      },
    },
  },
};
