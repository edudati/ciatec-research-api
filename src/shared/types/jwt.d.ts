import '@fastify/jwt';
import type { UserRole } from '@prisma/client';

declare module '@fastify/jwt' {
  interface FastifyJWT {
    payload: { sub: string; role: UserRole; iss: string; aud: string };
    user: { sub: string; role: UserRole; iss: string; aud: string };
  }
}
