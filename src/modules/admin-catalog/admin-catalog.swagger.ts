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
    is_deleted: { type: 'boolean' },
    created_at: { type: 'string', format: 'date-time' },
    updated_at: { type: 'string', format: 'date-time' },
  },
  required: ['id', 'name', 'description', 'is_active', 'is_deleted', 'created_at', 'updated_at'],
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
    is_deleted: { type: 'boolean' },
    created_at: { type: 'string', format: 'date-time' },
    updated_at: { type: 'string', format: 'date-time' },
  },
  required: ['id', 'game_id', 'name', 'description', 'is_default', 'is_active', 'is_deleted', 'created_at', 'updated_at'],
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
    is_deleted: { type: 'boolean' },
    created_at: { type: 'string', format: 'date-time' },
    updated_at: { type: 'string', format: 'date-time' },
  },
  required: ['id', 'preset_id', 'name', 'order', 'config', 'is_active', 'is_deleted', 'created_at', 'updated_at'],
} as const;

export const adminCatalogSwagger: Record<string, FastifySchema> = {
  listGames: {
    tags: ['Admin Catalog'],
    summary: 'List games (admin: includes inactive and soft-deleted)',
    security: [{ bearerAuth: [] }],
    response: {
      200: {
        type: 'object',
        properties: { games: { type: 'array', items: gameResponse } },
        required: ['games'],
      },
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Forbidden', ...appError },
    },
  },

  getGame: {
    tags: ['Admin Catalog'],
    summary: 'Get game (admin: includes inactive and soft-deleted)',
    security: [{ bearerAuth: [] }],
    response: {
      200: gameResponse,
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Forbidden', ...appError },
      404: { description: 'Game not found', ...appError },
    },
  },

  createGame: {
    tags: ['Admin Catalog'],
    summary: 'Create game (admin)',
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
    tags: ['Admin Catalog'],
    summary: 'Update game (admin)',
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
    tags: ['Admin Catalog'],
    summary: 'Soft delete game (admin; cascades presets/levels)',
    security: [{ bearerAuth: [] }],
    response: {
      204: { description: 'Deleted' },
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Forbidden', ...appError },
      404: { description: 'Game not found', ...appError },
    },
  },

  listPresets: {
    tags: ['Admin Catalog'],
    summary: 'List presets for game (admin: includes inactive and soft-deleted)',
    security: [{ bearerAuth: [] }],
    response: {
      200: { type: 'object', properties: { presets: { type: 'array', items: presetResponse } }, required: ['presets'] },
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Forbidden', ...appError },
      404: { description: 'Game not found', ...appError },
    },
  },

  getPreset: {
    tags: ['Admin Catalog'],
    summary: 'Get preset (admin: includes inactive and soft-deleted)',
    security: [{ bearerAuth: [] }],
    response: {
      200: presetResponse,
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Forbidden', ...appError },
      404: { description: 'Preset not found', ...appError },
    },
  },

  createPreset: {
    tags: ['Admin Catalog'],
    summary: 'Create preset (admin)',
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
    tags: ['Admin Catalog'],
    summary: 'Update preset (admin)',
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
    tags: ['Admin Catalog'],
    summary: 'Soft delete preset (admin; cascades levels)',
    security: [{ bearerAuth: [] }],
    response: {
      204: { description: 'Deleted' },
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Forbidden', ...appError },
      404: { description: 'Preset not found', ...appError },
    },
  },

  listLevels: {
    tags: ['Admin Catalog'],
    summary: 'List levels for preset (admin: includes inactive and soft-deleted)',
    security: [{ bearerAuth: [] }],
    response: {
      200: { type: 'object', properties: { levels: { type: 'array', items: levelResponse } }, required: ['levels'] },
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Forbidden', ...appError },
      404: { description: 'Preset not found', ...appError },
    },
  },

  getLevel: {
    tags: ['Admin Catalog'],
    summary: 'Get level (admin: includes inactive and soft-deleted)',
    security: [{ bearerAuth: [] }],
    response: {
      200: levelResponse,
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Forbidden', ...appError },
      404: { description: 'Level not found', ...appError },
    },
  },

  createLevel: {
    tags: ['Admin Catalog'],
    summary: 'Create level (admin)',
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
    tags: ['Admin Catalog'],
    summary: 'Update level (admin)',
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
    tags: ['Admin Catalog'],
    summary: 'Soft delete level (admin)',
    security: [{ bearerAuth: [] }],
    response: {
      204: { description: 'Deleted' },
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Forbidden', ...appError },
      404: { description: 'Level not found', ...appError },
    },
  },
};

