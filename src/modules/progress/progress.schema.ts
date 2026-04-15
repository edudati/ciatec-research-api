import { z } from 'zod';

export const startProgressQuerySchema = z.object({
  game_id: z.string().uuid(),
});

export type StartProgressQuery = z.infer<typeof startProgressQuerySchema>;
