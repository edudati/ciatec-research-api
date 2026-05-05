import type { FastifySchema } from 'fastify';

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

const telemetryAcceptedResponse = {
  description: 'Accepted',
  type: 'object',
  properties: {
    match_id: { type: 'string', format: 'uuid' },
    frames_received: { type: 'integer' },
    rows_inserted: { type: 'integer' },
  },
  required: ['match_id', 'frames_received', 'rows_inserted'],
} as const;

export const trunktiltSwagger: Record<string, FastifySchema> = {
  addWorldTelemetry: {
    tags: ['TrunkTilt'],
    summary: 'TrunkTilt world telemetry batch',
    description:
      'Stores typed world-state samples for a TrunkTilt match (ball, plane tilt, virtual input). Match must belong to TrunkTilt and not be finished. Idempotent per (match_id, frame_id).',
    security: [{ bearerAuth: [] }],
    params: {
      type: 'object',
      required: ['match_id'],
      properties: {
        match_id: { type: 'string', format: 'uuid' },
      },
    },
    body: {
      type: 'object',
      required: ['frames'],
      properties: {
        frames: {
          type: 'array',
          minItems: 1,
          maxItems: 200,
          items: { type: 'object', additionalProperties: true },
        },
      },
    },
    response: {
      202: telemetryAcceptedResponse,
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Not a TrunkTilt match', ...appError },
      404: { description: 'Match not found', ...appError },
      409: { description: 'Match already finished', ...appError },
    },
  },
  addPoseTelemetry: {
    tags: ['TrunkTilt'],
    summary: 'TrunkTilt pose landmarks batch',
    description:
      'Stores MediaPipe Pose landmarks per frame (`landmarks` array, 33 ids 0–32). Persisted in trunktilt_pose with landmark_id. Idempotent per (match_id, frame_id, landmark_id).',
    security: [{ bearerAuth: [] }],
    params: {
      type: 'object',
      required: ['match_id'],
      properties: {
        match_id: { type: 'string', format: 'uuid' },
      },
    },
    body: {
      type: 'object',
      required: ['frames'],
      properties: {
        frames: {
          type: 'array',
          minItems: 1,
          maxItems: 200,
          items: { type: 'object', additionalProperties: true },
        },
      },
    },
    response: {
      202: telemetryAcceptedResponse,
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Not a TrunkTilt match', ...appError },
      404: { description: 'Match not found', ...appError },
      409: { description: 'Match already finished', ...appError },
    },
  },
  addEvents: {
    tags: ['TrunkTilt'],
    summary: 'TrunkTilt discrete events batch',
    description:
      'Stores typed gameplay events in trunktilt_events (isolated from generic match_events). Match must be TrunkTilt and not finished.',
    security: [{ bearerAuth: [] }],
    params: {
      type: 'object',
      required: ['match_id'],
      properties: {
        match_id: { type: 'string', format: 'uuid' },
      },
    },
    body: {
      type: 'object',
      required: ['events'],
      properties: {
        events: {
          type: 'array',
          minItems: 1,
          maxItems: 500,
          items: { type: 'object', additionalProperties: true },
        },
      },
    },
    response: {
      201: {
        description: 'Events created',
        type: 'object',
        properties: {
          match_id: { type: 'string', format: 'uuid' },
          events_received: { type: 'integer' },
          events_created: { type: 'integer' },
        },
        required: ['match_id', 'events_received', 'events_created'],
      },
      400: { description: 'Validation (Zod)', ...zodValidationError },
      401: { description: 'Unauthorized', ...appError },
      403: { description: 'Not a TrunkTilt match', ...appError },
      404: { description: 'Match not found', ...appError },
      409: { description: 'Match already finished', ...appError },
    },
  },
};
