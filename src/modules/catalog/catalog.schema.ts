import { z } from 'zod';

export const gameIdParamsSchema = z.object({
  game_id: z.string().uuid(),
});

export const presetIdParamsSchema = z.object({
  preset_id: z.string().uuid(),
});

export const levelIdParamsSchema = z.object({
  level_id: z.string().uuid(),
});

export const createGameBodySchema = z
  .object({
    name: z.string().trim().min(1).max(128),
    description: z.string().trim().max(500).nullable().optional(),
    is_active: z.boolean().optional(),
  })
  .strict();

export const updateGameBodySchema = z
  .object({
    name: z.string().trim().min(1).max(128).optional(),
    description: z.string().trim().max(500).nullable().optional(),
    is_active: z.boolean().optional(),
  })
  .strict();

export const createPresetBodySchema = z
  .object({
    game_id: z.string().uuid(),
    name: z.string().trim().min(1).max(128),
    description: z.string().trim().max(500).nullable().optional(),
    is_default: z.boolean().optional(),
    is_active: z.boolean().optional(),
  })
  .strict();

export const updatePresetBodySchema = z
  .object({
    name: z.string().trim().min(1).max(128).optional(),
    description: z.string().trim().max(500).nullable().optional(),
    is_default: z.boolean().optional(),
    is_active: z.boolean().optional(),
  })
  .strict();

export const createLevelBodySchema = z
  .object({
    preset_id: z.string().uuid(),
    name: z.string().trim().min(1).max(128),
    order: z.number().int().nonnegative(),
    config: z.record(z.string(), z.unknown()).default({}),
    is_active: z.boolean().optional(),
  })
  .strict();

export const updateLevelBodySchema = z
  .object({
    name: z.string().trim().min(1).max(128).optional(),
    order: z.number().int().nonnegative().optional(),
    config: z.record(z.string(), z.unknown()).optional(),
    is_active: z.boolean().optional(),
  })
  .strict();

