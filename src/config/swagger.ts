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
      servers: [
        // Prefer same-origin so Swagger UI works when accessed via IP/localhost
        // and avoids browser blocks when the docs host differs from APP_URL.
        { url: '/', description: 'Same origin' },
        { url: serverUrl, description: 'Configured APP_URL' },
      ],
      tags: [
        { name: 'Health', description: 'Liveness' },
        { name: 'Auth', description: 'Authentication' },
        { name: 'Bubbles', description: 'bubbles — events, telemetry landmarks e world (JSON)' },
        { name: 'Bestbeat', description: 'bestbeat — events, telemetry landmarks e world (JSON)' },
        { name: 'TrunkTilt', description: 'TrunkTilt typed telemetry and events' },
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
