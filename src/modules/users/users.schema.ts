import { UserRole } from '@prisma/client';
import { z } from 'zod';

import { passwordSchema } from '../auth/auth.schema.js';

export const userRoles = [
  UserRole.ADMIN,
  UserRole.RESEARCHER,
  UserRole.PI,
  UserRole.PARTICIPANT,
  UserRole.PLAYER,
] as const;

const userRoleSchema = z.enum(userRoles);

export const listUsersQuerySchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  pageSize: z.coerce.number().int().min(1).max(100).default(10),
  q: z.preprocess(
    (v) => (typeof v === 'string' && v.trim() === '' ? undefined : v),
    z.string().trim().min(1).optional(),
  ),
  role: userRoleSchema.optional(),
  sort: z.enum(['createdAt', 'name', 'email', 'updatedAt']).default('createdAt'),
  order: z.enum(['asc', 'desc']).default('desc'),
});

export const userIdParamsSchema = z.object({
  id: z.string().uuid(),
});

export const createUserBodySchema = z.object({
  email: z.string().email(),
  password: passwordSchema,
  name: z.string().min(1),
  role: userRoleSchema,
});

export const patchUserBodySchema = z
  .object({
    name: z.string().min(1).optional(),
    role: userRoleSchema.optional(),
    email: z.string().email().optional(),
    password: passwordSchema.optional(),
    isFirstAccess: z.boolean().optional(),
  })
  .refine(
    (body) =>
      body.name !== undefined ||
      body.role !== undefined ||
      body.email !== undefined ||
      body.password !== undefined ||
      body.isFirstAccess !== undefined,
    { message: 'At least one field is required' },
  );

export type ListUsersQuery = z.infer<typeof listUsersQuerySchema>;
export type CreateUserBody = z.infer<typeof createUserBodySchema>;
export type PatchUserBody = z.infer<typeof patchUserBodySchema>;
