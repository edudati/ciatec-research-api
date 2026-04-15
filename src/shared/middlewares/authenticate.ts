import type { FastifyReply, FastifyRequest } from 'fastify';

import { UnauthorizedError } from '../errors/unauthorized-error.js';

export async function authenticate(
  request: FastifyRequest,
  _reply: FastifyReply,
): Promise<void> {
  try {
    await request.jwtVerify();
  } catch {
    throw new UnauthorizedError('Unauthorized');
  }
}
