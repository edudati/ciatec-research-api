import { z } from 'zod';

export const presetQuerySchema = z.object({
  game_id: z.string().uuid(),
});

export type PresetQuery = z.infer<typeof presetQuerySchema>;

export const levelParamsSchema = z.object({
  level_id: z.string().uuid(),
});

export type LevelParams = z.infer<typeof levelParamsSchema>;
