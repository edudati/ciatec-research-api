import { z } from 'zod';

export const finishMatchParamsSchema = z.object({
  match_id: z.string().uuid(),
});

/** Persisted under `client_meta` inside match_result_details.data. */
export const finishClientMetaSchema = z
  .object({
    app_version: z.string().max(128).optional(),
    unity_version: z.string().max(64).optional(),
    platform: z.string().max(64).optional(),
    device_model: z.string().max(128).optional(),
    locale: z.string().max(32).optional(),
  })
  .strict()
  .transform((o) => {
    const out: Record<string, string> = {};
    for (const [k, v] of Object.entries(o)) {
      if (typeof v === 'string') {
        const t = v.trim();
        if (t.length > 0) out[k] = t;
      }
    }
    return out;
  });

export const finishMatchBodySchema = z.object({
  score: z.number().int().nonnegative(),
  duration_ms: z.number().int().positive(),
  completed: z.boolean(),
  /** Same role as Idempotency-Key header when the client cannot set headers. */
  client_request_id: z.string().trim().min(1).max(128).optional(),
  client_meta: finishClientMetaSchema.optional(),
  extra: z.record(z.string(), z.unknown()).optional(),
});

export const getPresetQuerySchema = z.object({
  game_id: z.string().uuid(),
});

export const getLevelQuerySchema = z.object({
  preset_id: z.string().uuid(),
  level_id: z.string().uuid(),
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
