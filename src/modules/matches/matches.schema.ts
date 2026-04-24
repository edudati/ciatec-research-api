import { z } from 'zod';

export const finishMatchParamsSchema = z.object({
  match_id: z.string().uuid(),
});

export const finishMatchBodySchema = z.object({
  score: z.number().int().nonnegative(),
  duration_ms: z.number().int().positive(),
  completed: z.boolean(),
  extra: z.record(z.string(), z.unknown()).optional(),
});

const eventItemSchema = z.object({
  type: z.string().trim().min(1),
  timestamp: z.number().int().nonnegative(),
  data: z.record(z.string(), z.unknown()),
});

export const addMatchEventsBodySchema = z.object({
  events: z.array(eventItemSchema).min(1).max(500),
});

const telemetryFrameSchema = z.object({
  timestamp: z.number().int().nonnegative(),
  data: z.record(z.string(), z.unknown()),
});

export const addTelemetryLandmarksBodySchema = z.object({
  frames: z.array(telemetryFrameSchema).min(1).max(100),
});

const telemetryInputItemSchema = z.object({
  timestamp: z.number().int().nonnegative(),
  device: z.string().trim().min(1),
  data: z.record(z.string(), z.unknown()),
});

export const addTelemetryInputBodySchema = z.object({
  inputs: z.array(telemetryInputItemSchema).min(1).max(100),
});
