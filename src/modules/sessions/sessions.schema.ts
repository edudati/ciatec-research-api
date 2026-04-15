import { z } from 'zod';

export const createMatchBodySchema = z.object({
  game_id: z.string().uuid(),
  level_id: z.string().uuid(),
});
