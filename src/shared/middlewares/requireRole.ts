import type { FastifyReply, FastifyRequest } from 'fastify';

import type { UserRole } from '@prisma/client';

import { ForbiddenError } from '../errors/forbidden-error.js';

export function requireRole(...allowed: UserRole[]) {
  return async function requireRoleHandler(
    request: FastifyRequest,
    _reply: FastifyReply,
  ): Promise<void> {
    const role = request.user?.role;
    if (!role || !allowed.includes(role as UserRole)) {
      throw new ForbiddenError('Insufficient permissions');
    }
  };
}
