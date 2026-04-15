import { PrismaClient } from '@prisma/client';
import { PrismaPg } from '@prisma/adapter-pg';

import { env } from '../config/env.js';

declare global {
  // eslint-disable-next-line no-var
  var prisma: PrismaClient | undefined;
}

const adapter = new PrismaPg({ connectionString: env.DATABASE_URL });
export const prisma = globalThis.prisma ?? new PrismaClient({ adapter });

if (env.NODE_ENV !== 'production') {
  globalThis.prisma = prisma;
}
