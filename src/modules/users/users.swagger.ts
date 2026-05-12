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

const userRole = {
  type: 'string',
  enum: ['ADMIN', 'RESEARCHER', 'PI', 'PARTICIPANT', 'PLAYER'],
  description: 'Matches Prisma `UserRole`. Public register only creates PLAYER; this API can assign any role.',
} as const;

const userMeCore = {
  type: 'object',
  properties: {
    id: { type: 'string', format: 'uuid' },
    email: { type: 'string', format: 'email' },
    name: { type: 'string' },
    role: userRole,
    createdAt: { type: 'string', format: 'date-time' },
    emailVerified: { type: 'boolean' },
    isFirstAccess: { type: 'boolean' },
    totpEnabled: { type: 'boolean' },
  },
  required: ['id', 'email', 'name', 'role', 'createdAt', 'emailVerified', 'isFirstAccess', 'totpEnabled'],
} as const;

const userListItem = {
  type: 'object',
  properties: {
    ...userMeCore.properties,
    updatedAt: { type: 'string', format: 'date-time' },
  },
  required: [...userMeCore.required, 'updatedAt'],
} as const;

const userDetail = {
  type: 'object',
  properties: {
    ...userMeCore.properties,
    updatedAt: { type: 'string', format: 'date-time' },
    deletedAt: { anyOf: [{ type: 'string', format: 'date-time' }, { type: 'null' }] },
  },
  required: [...userMeCore.required, 'updatedAt', 'deletedAt'],
} as const;

export const usersSwagger: Record<string, FastifySchema> = {
  listUsers: {
    tags: ['Users'],
    summary: 'List users',
    description:
      'Paginated list of users that are not soft-deleted and have credentials. `total` matches the same filters. A soft-deleted account still reserves its email until restored or changed elsewhere.',
    security: [{ bearerAuth: [] }],
    querystring: {
      type: 'object',
      properties: {
        page: { type: 'integer', minimum: 1, default: 1 },
        pageSize: { type: 'integer', minimum: 1, maximum: 100, default: 10 },
        q: { type: 'string', description: 'Case-insensitive match on name or email' },
        role: userRole,
        sort: {
          type: 'string',
          enum: ['createdAt', 'name', 'email', 'updatedAt'],
          default: 'createdAt',
        },
        order: { type: 'string', enum: ['asc', 'desc'], default: 'desc' },
      },
    },
    response: {
      200: {
        description: 'OK',
        type: 'object',
        properties: {
          users: { type: 'array', items: userListItem },
          total: { type: 'integer' },
          page: { type: 'integer' },
          pageSize: { type: 'integer' },
        },
        required: ['users', 'total', 'page', 'pageSize'],
      },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
    },
  },

  getUser: {
    tags: ['Users'],
    summary: 'Get user by id',
    description: 'Same core fields as `GET /auth/me`, plus `updatedAt` and `deletedAt` (null if active).',
    security: [{ bearerAuth: [] }],
    params: {
      type: 'object',
      required: ['id'],
      properties: { id: { type: 'string', format: 'uuid' } },
    },
    response: {
      200: { description: 'OK', ...userDetail },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      404: { description: 'User not found', ...appError },
    },
  },

  createUser: {
    tags: ['Users'],
    summary: 'Create user (signup-style)',
    description:
      'Creates `User` + `AuthUser`. Password rules match public register: min 8 chars, one uppercase letter, one digit.',
    security: [{ bearerAuth: [] }],
    body: {
      type: 'object',
      required: ['email', 'password', 'name', 'role'],
      properties: {
        email: { type: 'string', format: 'email' },
        password: { type: 'string', minLength: 8 },
        name: { type: 'string', minLength: 1 },
        role: userRole,
      },
    },
    response: {
      201: { description: 'Created', ...userDetail },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      409: { description: 'Email already in use', ...appError },
    },
  },

  updateUser: {
    tags: ['Users'],
    summary: 'Update user',
    description: 'Partial update. At least one field required. Cannot update a soft-deleted user.',
    security: [{ bearerAuth: [] }],
    params: {
      type: 'object',
      required: ['id'],
      properties: { id: { type: 'string', format: 'uuid' } },
    },
    body: {
      type: 'object',
      properties: {
        name: { type: 'string', minLength: 1 },
        role: userRole,
        email: { type: 'string', format: 'email' },
        password: { type: 'string', minLength: 8 },
        isFirstAccess: { type: 'boolean' },
      },
    },
    response: {
      200: { description: 'OK', ...userDetail },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      404: { description: 'User not found', ...appError },
      409: { description: 'Email already in use', ...appError },
    },
  },

  deleteUser: {
    tags: ['Users'],
    summary: 'Delete user',
    description: 'Sets `deletedAt`. Idempotent if the user is already deleted.',
    security: [{ bearerAuth: [] }],
    params: {
      type: 'object',
      required: ['id'],
      properties: { id: { type: 'string', format: 'uuid' } },
    },
    response: {
      204: { description: 'No content' },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      404: { description: 'User not found', ...appError },
    },
  },
};
