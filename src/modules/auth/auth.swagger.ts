import type { FastifySchema } from 'fastify';

const userRole = {
  type: 'string',
  enum: ['ADMIN', 'RESEARCHER', 'PI', 'PARTICIPANT', 'PLAYER'],
  description:
    'Prisma `UserRole`. Public `POST /auth/register` always creates PLAYER; other roles come from admin flows, `POST /api/v1/users`, seed, or DB.',
  example: 'PLAYER',
} as const;

const userPublic = {
  type: 'object',
  properties: {
    id: { type: 'string', format: 'uuid' },
    email: { type: 'string', format: 'email' },
    name: { type: 'string' },
    role: userRole,
    createdAt: { type: 'string', format: 'date-time' },
    emailVerified: {
      type: 'boolean',
      description:
        'True when `emailVerifiedAt` is set on the credential row. Today all new password signups set this immediately; TODO: real email verification before setting.',
    },
    isFirstAccess: {
      type: 'boolean',
      description: 'Onboarding hint; clear via `PATCH /api/v1/users/:id` when the client completes first-run.',
    },
    totpEnabled: {
      type: 'boolean',
      description: 'Whether TOTP (authenticator app) is enabled. TODO: enforce second step on login when true.',
    },
  },
  required: ['id', 'email', 'name', 'role', 'createdAt', 'emailVerified', 'isFirstAccess', 'totpEnabled'],
} as const;

const authPairResponse = {
  type: 'object',
  properties: {
    user: userPublic,
    accessToken: { type: 'string' },
    refreshToken: { type: 'string' },
  },
  required: ['user', 'accessToken', 'refreshToken'],
} as const;

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

export const authSwagger: Record<string, FastifySchema> = {
  register: {
    tags: ['Auth'],
    summary: 'Register',
    description:
      'Creates a user with role PLAYER. Password: min 8 characters, at least one uppercase letter and one digit. A soft-deleted account still reserves its email until the address is changed or the row is removed from the database. `emailVerified` is set true at signup for now; TODO: send confirmation email and set only after verify.',
    body: {
      type: 'object',
      required: ['email', 'password', 'name'],
      properties: {
        email: { type: 'string', format: 'email' },
        password: { type: 'string', minLength: 8 },
        name: { type: 'string', minLength: 1 },
      },
    },
    response: {
      201: { description: 'Created', ...authPairResponse },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      409: { description: 'Email already in use', ...appError },
    },
  },

  login: {
    tags: ['Auth'],
    summary: 'Login',
    description: 'Invalid email or password returns the same error message (security).',
    body: {
      type: 'object',
      required: ['email', 'password'],
      properties: {
        email: { type: 'string', format: 'email' },
        password: { type: 'string' },
      },
    },
    response: {
      200: { description: 'OK', ...authPairResponse },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Invalid credentials', ...appError },
    },
  },

  refresh: {
    tags: ['Auth'],
    summary: 'Refresh tokens',
    description:
      'Rotates the refresh token: the previous refresh row is revoked and a new pair is returned.',
    body: {
      type: 'object',
      required: ['refreshToken'],
      properties: {
        refreshToken: { type: 'string' },
      },
    },
    response: {
      200: {
        description: 'OK',
        type: 'object',
        properties: {
          accessToken: { type: 'string' },
          refreshToken: { type: 'string' },
        },
        required: ['accessToken', 'refreshToken'],
      },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Invalid or expired refresh', ...appError },
    },
  },

  logout: {
    tags: ['Auth'],
    summary: 'Logout',
    description:
      'Requires Bearer access token. If `refreshToken` is sent, only that session is revoked; otherwise all refresh tokens for the user are revoked.',
    security: [{ bearerAuth: [] }],
    body: {
      type: 'object',
      properties: {
        refreshToken: { type: 'string' },
      },
    },
    response: {
      204: { description: 'No content' },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Missing or invalid access token', ...appError },
    },
  },

  me: {
    tags: ['Auth'],
    summary: 'Current user',
    description: 'Profile for the access token subject (`sub`). Same shape as `user` in register/login.',
    security: [{ bearerAuth: [] }],
    response: {
      200: {
        description: 'OK',
        ...userPublic,
      },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Missing or invalid access token', ...appError },
      404: { description: 'User not found', ...appError },
    },
  },
};
