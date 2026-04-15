import cors from '@fastify/cors';
import helmet from '@fastify/helmet';
import fastifyJwt from '@fastify/jwt';
import swagger from '@fastify/swagger';
import swaggerUi from '@fastify/swagger-ui';
import Fastify, {
  type FastifyInstance,
  type FastifyPluginCallback,
  type FastifyRequest,
} from 'fastify';
import { ZodError } from 'zod';

import { env } from './config/env.js';
import { buildSwaggerOptions } from './config/swagger.js';
import { authRoutes } from './modules/auth/auth.routes.js';
import { matchesRoutes } from './modules/matches/matches.routes.js';
import { progressRoutes } from './modules/progress/progress.routes.js';
import { sessionsRoutes } from './modules/sessions/sessions.routes.js';
import { AppError } from './shared/errors/app-error.js';

type JwtPluginOptions = {
  secret: string;
  sign: {
    expiresIn: string;
    issuer: string;
    audience: string;
  };
  verify: {
    issuer: string;
    audience: string;
  };
};

const SENSITIVE_KEYS = new Set(['password', 'token', 'refreshToken', 'authorization']);

function sanitizeLogValue(value: unknown): unknown {
  if (value === null || value === undefined) {
    return value;
  }
  if (Array.isArray(value)) {
    return value.map(sanitizeLogValue);
  }
  if (typeof value === 'object') {
    const input = value as Record<string, unknown>;
    const output: Record<string, unknown> = {};
    for (const [key, innerValue] of Object.entries(input)) {
      if (SENSITIVE_KEYS.has(key)) {
        output[key] = '***';
        continue;
      }
      output[key] = sanitizeLogValue(innerValue);
    }
    return output;
  }
  return value;
}

export function buildApp(): FastifyInstance {
  const app = Fastify({
    logger: true,
  });
  const API_PREFIX = '/api/v1';
  const requestStartTimes = new WeakMap<FastifyRequest, bigint>();

  app.addHook('onRequest', (request, _reply, done) => {
    requestStartTimes.set(request, process.hrtime.bigint());
    done();
  });

  app.addHook('preHandler', (request, _reply, done) => {
    request.log.info(
      {
        event: 'request_in',
        method: request.method,
        url: request.url,
        query: sanitizeLogValue(request.query),
        params: sanitizeLogValue(request.params),
        body: sanitizeLogValue(request.body),
      },
      'Incoming request',
    );
    done();
  });

  app.addHook('onResponse', (request, reply, done) => {
    const startTime = requestStartTimes.get(request);
    const durationMs =
      startTime === undefined ? undefined : Number(process.hrtime.bigint() - startTime) / 1_000_000;

    request.log.info(
      {
        event: 'request_out',
        method: request.method,
        url: request.url,
        status_code: reply.statusCode,
        duration_ms: durationMs === undefined ? undefined : Math.round(durationMs * 100) / 100,
      },
      'Request finished',
    );
    done();
  });

  app.register(cors, { origin: true });
  app.register(helmet, {
    contentSecurityPolicy: false,
  });

  void app.register(swagger, buildSwaggerOptions());

  const jwtOptions: JwtPluginOptions = {
    secret: env.JWT_SECRET,
    sign: {
      expiresIn: env.JWT_EXPIRES_IN,
      issuer: env.JWT_ISSUER,
      audience: env.JWT_AUDIENCE,
    },
    verify: {
      issuer: env.JWT_ISSUER,
      audience: env.JWT_AUDIENCE,
    },
  };

  void app.register(
    fastifyJwt as unknown as FastifyPluginCallback<JwtPluginOptions>,
    jwtOptions,
  );
  void app.register(authRoutes, { prefix: `${API_PREFIX}/auth` });
  void app.register(matchesRoutes, { prefix: `${API_PREFIX}/matches` });
  void app.register(progressRoutes, { prefix: `${API_PREFIX}/progress` });
  void app.register(sessionsRoutes, { prefix: `${API_PREFIX}/sessions` });

  app.get(
    '/health',
    {
      schema: {
        tags: ['Health'],
        summary: 'Health check',
        response: {
          200: {
            description: 'OK',
            type: 'object',
            properties: {
              status: { type: 'string', example: 'ok' },
              timestamp: { type: 'string', format: 'date-time' },
            },
            required: ['status', 'timestamp'],
          },
        },
      },
    },
    async () => ({
      status: 'ok',
      timestamp: new Date().toISOString(),
    }),
  );

  void app.register(swaggerUi, {
    routePrefix: '/docs',
    uiConfig: {
      docExpansion: 'list',
      deepLinking: true,
    },
  });

  app.setErrorHandler((error, request, reply) => {
    const errorData = error instanceof Error ? error : new Error('Unknown error');

    request.log.error(
      {
        event: 'request_error',
        method: request.method,
        url: request.url,
        error_name: errorData.name,
        error_message: errorData.message,
      },
      'Request failed',
    );

    if (error instanceof ZodError) {
      return reply.status(400).send({
        success: false,
        code: 'VALIDATION_ERROR',
        message: 'Validation error',
        details: error.issues,
        issues: error.issues,
      });
    }

    if (error instanceof AppError) {
      return reply.status(error.statusCode).send({
        success: false,
        code: error.code,
        message: error.message,
      });
    }

    app.log.error(error);
    return reply.status(500).send({
      success: false,
      code: 'INTERNAL_ERROR',
      message: 'Internal server error',
    });
  });

  return app;
}
