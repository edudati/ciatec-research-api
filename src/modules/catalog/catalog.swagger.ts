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

const gameResponse = {
  type: 'object',
  properties: {
    id: { type: 'string', format: 'uuid' },
    name: { type: 'string' },
    description: { anyOf: [{ type: 'string' }, { type: 'null' }] },
    is_active: { type: 'boolean' },
    created_at: { type: 'string', format: 'date-time' },
    updated_at: { type: 'string', format: 'date-time' },
  },
  required: ['id', 'name', 'description', 'is_active', 'created_at', 'updated_at'],
} as const;

const presetResponse = {
  type: 'object',
  properties: {
    id: { type: 'string', format: 'uuid' },
    game_id: { type: 'string', format: 'uuid' },
    name: { type: 'string' },
    description: { anyOf: [{ type: 'string' }, { type: 'null' }] },
    is_default: { type: 'boolean' },
    is_active: { type: 'boolean' },
    created_at: { type: 'string', format: 'date-time' },
    updated_at: { type: 'string', format: 'date-time' },
  },
  required: ['id', 'game_id', 'name', 'description', 'is_default', 'is_active', 'created_at', 'updated_at'],
} as const;

const levelResponse = {
  type: 'object',
  properties: {
    id: { type: 'string', format: 'uuid' },
    preset_id: { type: 'string', format: 'uuid' },
    name: { type: 'string' },
    order: { type: 'integer' },
    config: { type: 'object', additionalProperties: true },
    is_active: { type: 'boolean' },
    created_at: { type: 'string', format: 'date-time' },
    updated_at: { type: 'string', format: 'date-time' },
  },
  required: ['id', 'preset_id', 'name', 'order', 'config', 'is_active', 'created_at', 'updated_at'],
} as const;

export const catalogSwagger: Record<string, FastifySchema> = {
  listGames: {
    tags: ['Catalog'],
    summary: 'List games (active only)',
    security: [{ bearerAuth: [] }],
    response: {
      200: {
        type: 'object',
        properties: { games: { type: 'array', items: gameResponse } },
        required: ['games'],
      },
      401: { description: 'Unauthorized', ...appError },
    },
  },

  getGame: {
    tags: ['Catalog'],
    summary: 'Get game (active only)',
    security: [{ bearerAuth: [] }],
    response: {
      200: gameResponse,
      401: { description: 'Unauthorized', ...appError },
      404: { description: 'Game not found', ...appError },
    },
  },

  createGame: {
    tags: ['Catalog'],
    summary: 'Create game',
    security: [{ bearerAuth: [] }],
    body: {
      type: 'object',
      required: ['name'],
      properties: {
        name: { type: 'string' },
        description: { anyOf: [{ type: 'string' }, { type: 'null' }] },
        is_active: { type: 'boolean' },
      },
    },
    response: {
      201: gameResponse,
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Forbidden', ...appError },
    },
  },

  updateGame: {
    tags: ['Catalog'],
    summary: 'Update game',
    security: [{ bearerAuth: [] }],
    body: {
      type: 'object',
      properties: {
        name: { type: 'string' },
        description: { anyOf: [{ type: 'string' }, { type: 'null' }] },
        is_active: { type: 'boolean' },
      },
    },
    response: {
      200: gameResponse,
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Forbidden', ...appError },
      404: { description: 'Game not found', ...appError },
    },
  },

  deleteGame: {
    tags: ['Catalog'],
    summary: 'Soft delete game (cascades presets/levels)',
    security: [{ bearerAuth: [] }],
    response: {
      204: { description: 'Deleted' },
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Forbidden', ...appError },
      404: { description: 'Game not found', ...appError },
    },
  },

  listPresets: {
    tags: ['Catalog'],
    summary: 'List presets for game (active only)',
    security: [{ bearerAuth: [] }],
    response: {
      200: { type: 'object', properties: { presets: { type: 'array', items: presetResponse } }, required: ['presets'] },
      401: { description: 'Unauthorized', ...appError },
      404: { description: 'Game not found', ...appError },
    },
  },

  getPreset: {
    tags: ['Catalog'],
    summary: 'Get preset (active only)',
    security: [{ bearerAuth: [] }],
    response: {
      200: presetResponse,
      401: { description: 'Unauthorized', ...appError },
      404: { description: 'Preset not found', ...appError },
    },
  },

  createPreset: {
    tags: ['Catalog'],
    summary: 'Create preset',
    security: [{ bearerAuth: [] }],
    body: {
      type: 'object',
      required: ['game_id', 'name'],
      properties: {
        game_id: { type: 'string', format: 'uuid' },
        name: { type: 'string' },
        description: { anyOf: [{ type: 'string' }, { type: 'null' }] },
        is_default: { type: 'boolean' },
        is_active: { type: 'boolean' },
      },
    },
    response: {
      201: presetResponse,
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Forbidden', ...appError },
      404: { description: 'Game not found', ...appError },
    },
  },

  updatePreset: {
    tags: ['Catalog'],
    summary: 'Update preset',
    security: [{ bearerAuth: [] }],
    body: {
      type: 'object',
      properties: {
        name: { type: 'string' },
        description: { anyOf: [{ type: 'string' }, { type: 'null' }] },
        is_default: { type: 'boolean' },
        is_active: { type: 'boolean' },
      },
    },
    response: {
      200: presetResponse,
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Forbidden', ...appError },
      404: { description: 'Preset not found', ...appError },
    },
  },

  deletePreset: {
    tags: ['Catalog'],
    summary: 'Soft delete preset (cascades levels)',
    security: [{ bearerAuth: [] }],
    response: {
      204: { description: 'Deleted' },
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Forbidden', ...appError },
      404: { description: 'Preset not found', ...appError },
    },
  },

  listLevels: {
    tags: ['Catalog'],
    summary: 'List levels for preset (active only)',
    security: [{ bearerAuth: [] }],
    response: {
      200: { type: 'object', properties: { levels: { type: 'array', items: levelResponse } }, required: ['levels'] },
      401: { description: 'Unauthorized', ...appError },
      404: { description: 'Preset not found', ...appError },
    },
  },

  getLevel: {
    tags: ['Catalog'],
    summary: 'Get level (active only)',
    security: [{ bearerAuth: [] }],
    response: {
      200: levelResponse,
      401: { description: 'Unauthorized', ...appError },
      404: { description: 'Level not found', ...appError },
    },
  },

  createLevel: {
    tags: ['Catalog'],
    summary: 'Create level',
    security: [{ bearerAuth: [] }],
    body: {
      type: 'object',
      required: ['preset_id', 'name', 'order', 'config'],
      properties: {
        preset_id: { type: 'string', format: 'uuid' },
        name: { type: 'string' },
        order: { type: 'integer' },
        config: { type: 'object', additionalProperties: true },
        is_active: { type: 'boolean' },
      },
    },
    response: {
      201: levelResponse,
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Forbidden', ...appError },
      404: { description: 'Preset not found', ...appError },
    },
  },

  updateLevel: {
    tags: ['Catalog'],
    summary: 'Update level',
    security: [{ bearerAuth: [] }],
    body: {
      type: 'object',
      properties: {
        name: { type: 'string' },
        order: { type: 'integer' },
        config: { type: 'object', additionalProperties: true },
        is_active: { type: 'boolean' },
      },
    },
    response: {
      200: levelResponse,
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Forbidden', ...appError },
      404: { description: 'Level not found', ...appError },
    },
  },

  deleteLevel: {
    tags: ['Catalog'],
    summary: 'Soft delete level',
    security: [{ bearerAuth: [] }],
    response: {
      204: { description: 'Deleted' },
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Forbidden', ...appError },
      404: { description: 'Level not found', ...appError },
    },
  },
};

