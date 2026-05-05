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

const telemetryLandmarkFrameSchema = z.object({
  timestamp: z.number().int().nonnegative(),
  data: z.record(z.string(), z.unknown()),
});

/** Batch JSON por frame — típico: dados de landmarks MediaPipe em `data`. */
export const addTelemetryLandmarksBodySchema = z.object({
  frames: z.array(telemetryLandmarkFrameSchema).min(1).max(100),
});

const telemetryWorldFrameSchema = z.object({
  timestamp: z.number().int().nonnegative(),
  device: z.string().trim().min(1),
  data: z.record(z.string(), z.unknown()),
});

export const addTelemetryWorldBodySchema = z.object({
  frames: z.array(telemetryWorldFrameSchema).min(1).max(100),
});
