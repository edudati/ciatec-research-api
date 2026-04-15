import type { FastifyInstance } from 'fastify';

import { env } from '../../config/env.js';
import { prisma } from '../../lib/prisma.js';
import { authenticate } from '../../shared/middlewares/authenticate.js';
import { createAuthController } from './auth.controller.js';
import { createAuthService } from './auth.service.js';
import { authSwagger } from './auth.swagger.js';

export async function authRoutes(fastify: FastifyInstance): Promise<void> {
  const authService = createAuthService({
    prisma,
    signAccessToken: (payload) =>
      fastify.jwt.sign({
        sub: payload.sub,
        role: payload.role,
        iss: env.JWT_ISSUER,
        aud: env.JWT_AUDIENCE,
      }),
  });

  const controller = createAuthController(authService);

  fastify.post('/register', { schema: authSwagger.register }, controller.register);
  fastify.post('/login', { schema: authSwagger.login }, controller.login);
  fastify.post('/refresh', { schema: authSwagger.refresh }, controller.refresh);
  fastify.post(
    '/logout',
    { preHandler: [authenticate], schema: authSwagger.logout },
    controller.logout,
  );
  fastify.get('/me', { preHandler: [authenticate], schema: authSwagger.me }, controller.me);
}
