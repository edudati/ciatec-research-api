import 'dotenv/config';

import { PrismaPg } from '@prisma/adapter-pg';
import { PrismaClient } from '@prisma/client';

if (!process.env.DATABASE_URL) {
  throw new Error('DATABASE_URL nao definida para executar seed.');
}

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL });
const prisma = new PrismaClient({ adapter });

export const BUBLI_GAME_ID = 'd601b66e-2f7d-42bd-b7e2-11baa208faf3';
export const BUBLI_PRESET_ID = '0ed90aca-1200-4781-b11f-0368ca417b17';
export const BUBLI_LEVEL_1_ID = 'c7476ec4-2bc5-4fee-afde-648e82fef278';
export const BUBLI_LEVEL_2_ID = 'bcb50b2d-769a-4a52-82f7-9dda7f52adf3';
export const BUBLI_LEVEL_3_ID = 'ee5bfb25-4f6f-4355-a050-ece42e0dc9ac';

async function seedBubli() {
  await prisma.game.upsert({
    where: { id: BUBLI_GAME_ID },
    update: {
      name: 'Bubli',
      description: 'Jogo base Bubli para integracao Unity.',
    },
    create: {
      id: BUBLI_GAME_ID,
      name: 'Bubli',
      description: 'Jogo base Bubli para integracao Unity.',
    },
  });

  await prisma.preset.upsert({
    where: { id: BUBLI_PRESET_ID },
    update: {
      gameId: BUBLI_GAME_ID,
      name: 'Preset Padrao',
      description: 'Preset inicial padrao do Bubli.',
    },
    create: {
      id: BUBLI_PRESET_ID,
      gameId: BUBLI_GAME_ID,
      name: 'Preset Padrao',
      description: 'Preset inicial padrao do Bubli.',
    },
  });

  await prisma.level.upsert({
    where: { id: BUBLI_LEVEL_1_ID },
    update: {
      presetId: BUBLI_PRESET_ID,
      name: 'Nivel 1',
      order: 1,
      config: {},
    },
    create: {
      id: BUBLI_LEVEL_1_ID,
      presetId: BUBLI_PRESET_ID,
      name: 'Nivel 1',
      order: 1,
      config: {},
    },
  });

  await prisma.level.upsert({
    where: { id: BUBLI_LEVEL_2_ID },
    update: {
      presetId: BUBLI_PRESET_ID,
      name: 'Nivel 2',
      order: 2,
      config: {},
    },
    create: {
      id: BUBLI_LEVEL_2_ID,
      presetId: BUBLI_PRESET_ID,
      name: 'Nivel 2',
      order: 2,
      config: {},
    },
  });

  await prisma.level.upsert({
    where: { id: BUBLI_LEVEL_3_ID },
    update: {
      presetId: BUBLI_PRESET_ID,
      name: 'Nivel 3',
      order: 3,
      config: {},
    },
    create: {
      id: BUBLI_LEVEL_3_ID,
      presetId: BUBLI_PRESET_ID,
      name: 'Nivel 3',
      order: 3,
      config: {},
    },
  });
}

async function main() {
  await seedBubli();
  console.log('Seed concluido com sucesso.');
  console.log(`BUBLI_GAME_ID=${BUBLI_GAME_ID}`);
}

main()
  .catch((error) => {
    console.error('Falha ao executar seed:', error);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
