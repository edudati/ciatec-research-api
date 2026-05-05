import type { SwaggerOptions } from '@fastify/swagger';

import { env } from './env.js';

const serverUrl = env.APP_URL.replace(/\/$/, '');

export function buildSwaggerOptions(): SwaggerOptions {
  return {
    openapi: {
      openapi: '3.0.3',
      info: {
        title: 'Ciatec Research API',
        description:
          'REST API. Auth uses access (Bearer) + refresh JWTs; see `docs/AUTH-FLOW.md` for client flow.',
        version: '1.0.0',
      },
      servers: [{ url: serverUrl, description: 'This server' }],
      tags: [
        { name: 'Health', description: 'Liveness' },
        { name: 'Auth', description: 'Authentication' },
        { name: 'Progress', description: 'Preset trail and level config (gameplay)' },
      ],
      components: {
        securitySchemes: {
          bearerAuth: {
            type: 'http',
            scheme: 'bearer',
            bearerFormat: 'JWT',
            description: 'Access token from login, register, or refresh.',
          },
        },
      },
    },
    hideUntagged: false,
  };
}
