import { z } from 'zod';

export const startProgressQuerySchema = z.object({
  game_id: z.string().uuid(),
  /** `summary` omits per-level `config` on the trail; `current_level` still includes `config`. */
  levels_detail: z.enum(['summary', 'full']).optional().default('summary'),
});

export type StartProgressQuery = z.infer<typeof startProgressQuerySchema>;
