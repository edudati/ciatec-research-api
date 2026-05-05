import { z } from 'zod';

export const trunktiltMatchParamsSchema = z.object({
  match_id: z.string().uuid(),
});

const vec3Schema = z.object({
  x: z.number(),
  y: z.number(),
  z: z.number(),
});

export const addTrunktiltWorldBodySchema = z.object({
  frames: z
    .array(
      z.object({
        timestampMs: z.number().int().nonnegative(),
        frameId: z.number().int().nonnegative(),
        ballPosition: vec3Schema,
        ballVelocity: vec3Schema,
        velocityMagnitude: z.number(),
        accelerationMagnitude: z.number(),
        planeTiltX: vec3Schema,
        planeTiltZ: vec3Schema,
        inputVirtualX: z.number(),
        inputVirtualZ: z.number(),
      }),
    )
    .min(1)
    .max(200),
});

/** Um ponto MediaPipe Pose (landmark index 0–32). */
const mediaPipeLandmarkSchema = z.object({
  id: z.number().int().min(0).max(32),
  x: z.number(),
  y: z.number(),
  z: z.number(),
  visibility: z.number().min(0).max(1).nullable().optional(),
});

const trunktiltPoseFrameSchema = z
  .object({
    timestampMs: z.number().int().nonnegative(),
    frameId: z.number().int().nonnegative(),
    landmarks: z.array(mediaPipeLandmarkSchema).length(33),
  })
  .refine(
    (frame) => {
      const ids = new Set(frame.landmarks.map((l) => l.id));
      if (ids.size !== 33) return false;
      for (let i = 0; i <= 32; i++) {
        if (!ids.has(i)) return false;
      }
      return true;
    },
    { message: 'Each frame must include MediaPipe landmarks with ids 0–32 exactly once' },
  );

export const addTrunktiltPoseBodySchema = z.object({
  frames: z.array(trunktiltPoseFrameSchema).min(1).max(200),
});

export const trunktiltEventItemSchema = z.discriminatedUnion('type', [
  z.object({
    type: z.literal('COIN_COLLECTED'),
    timestamp: z.number().int().nonnegative(),
    data: z.object({
      x: z.number(),
      y: z.number(),
      z: z.number(),
      value: z.number(),
    }),
  }),
  z.object({
    type: z.literal('CHECKPOINT_REACHED'),
    timestamp: z.number().int().nonnegative(),
    data: vec3Schema,
  }),
  z.object({
    type: z.literal('FALL_OCCURRED'),
    timestamp: z.number().int().nonnegative(),
    data: vec3Schema,
  }),
  z.object({
    type: z.literal('LEVEL_COMPLETED'),
    timestamp: z.number().int().nonnegative(),
    data: z.record(z.string(), z.unknown()),
  }),
  z.object({
    type: z.literal('LEVEL_FAILED'),
    timestamp: z.number().int().nonnegative(),
    data: z.record(z.string(), z.unknown()),
  }),
  z.object({
    type: z.literal('LEVEL_STARTED'),
    timestamp: z.number().int().nonnegative(),
    data: z.record(z.string(), z.unknown()),
  }),
  z.object({
    type: z.literal('LEVEL_TIMER_STARTED'),
    timestamp: z.number().int().nonnegative(),
    data: z.record(z.string(), z.unknown()),
  }),
]);

export const addTrunktiltEventsBodySchema = z.object({
  events: z.array(trunktiltEventItemSchema).min(1).max(500),
});
