import 'dotenv/config';

import { PrismaPg } from '@prisma/adapter-pg';
import { Prisma, PrismaClient } from '@prisma/client';

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

/** Bestbeat (novo jogo). IDs fixos para o cliente e documentação. */
export const BESTBEAT_GAME_ID = 'e802c4a6-1b2d-4e3f-8a9b-0c1d2e3f4a5b';
export const BESTBEAT_PRESET_ID = 'f912d5b7-2c3e-4f4a-9b0a-1d2e3f4a5b6c';
export const BESTBEAT_LEVEL_1_ID = '0a23e6c8-3d4f-4a5b-0b1a-2e3f4a5b6c7d';
export const BESTBEAT_LEVEL_2_ID = '1b34f7d9-4e5a-4b6c-0d1e-2f3a4b5c6d7e';

/** Config default do preset bestbeat (sequence + targets). */
const BESTBEAT_LEVEL_1_CONFIG: Prisma.InputJsonValue = {
  mode: 'sequence',
  targets: [
    {
      id: 1,
      x: -0.3,
      y: 0.0,
      radius: 0.08,
      color_id: 'blue',
      opacity: 1.0,
      skin: 'default',
      pulse: false,
    },
    {
      id: 2,
      x: 0.3,
      y: 0.0,
      radius: 0.08,
      color_id: 'blue',
      opacity: 1.0,
      skin: 'default',
      pulse: false,
    },
  ],
  sequence: [
    {
      target_id: 1,
      order: 0,
      spawn_delay_ms: 0,
      mature_time_ms: 2000,
      warning_time_ms: 500,
      destroy_time_ms: 300,
    },
    {
      target_id: 2,
      order: 1,
      spawn_delay_ms: 500,
      mature_time_ms: 2000,
      warning_time_ms: 500,
      destroy_time_ms: 300,
    },
    {
      target_id: 1,
      order: 2,
      spawn_delay_ms: 500,
      mature_time_ms: 2000,
      warning_time_ms: 500,
      destroy_time_ms: 300,
    },
    {
      target_id: 2,
      order: 3,
      spawn_delay_ms: 500,
      mature_time_ms: 2000,
      warning_time_ms: 500,
      destroy_time_ms: 300,
    },
  ],
};

const BESTBEAT_LEVEL_2_CONFIG: Prisma.InputJsonValue = {
  mode: 'sequence',
  targets: [
    {
      id: 1,
      x: -0.3,
      y: -0.3,
      radius: 0.08,
      color_id: 'blue',
      opacity: 1.0,
      skin: 'default',
      pulse: false,
    },
    {
      id: 2,
      x: 0.3,
      y: -0.3,
      radius: 0.08,
      color_id: 'blue',
      opacity: 1.0,
      skin: 'default',
      pulse: false,
    },
    {
      id: 3,
      x: 0.3,
      y: 0.3,
      radius: 0.08,
      color_id: 'blue',
      opacity: 1.0,
      skin: 'default',
      pulse: false,
    },
    {
      id: 4,
      x: -0.3,
      y: 0.3,
      radius: 0.08,
      color_id: 'blue',
      opacity: 1.0,
      skin: 'default',
      pulse: false,
    },
  ],
  sequence: [
    {
      target_id: 1,
      order: 0,
      spawn_delay_ms: 0,
      mature_time_ms: 2000,
      warning_time_ms: 500,
      destroy_time_ms: 300,
    },
    {
      target_id: 2,
      order: 1,
      spawn_delay_ms: 500,
      mature_time_ms: 2000,
      warning_time_ms: 500,
      destroy_time_ms: 300,
    },
    {
      target_id: 3,
      order: 2,
      spawn_delay_ms: 500,
      mature_time_ms: 2000,
      warning_time_ms: 500,
      destroy_time_ms: 300,
    },
    {
      target_id: 4,
      order: 3,
      spawn_delay_ms: 500,
      mature_time_ms: 2000,
      warning_time_ms: 500,
      destroy_time_ms: 300,
    },
    {
      target_id: 1,
      order: 4,
      spawn_delay_ms: 500,
      mature_time_ms: 2000,
      warning_time_ms: 500,
      destroy_time_ms: 300,
    },
    {
      target_id: 2,
      order: 5,
      spawn_delay_ms: 500,
      mature_time_ms: 2000,
      warning_time_ms: 500,
      destroy_time_ms: 300,
    },
    {
      target_id: 3,
      order: 6,
      spawn_delay_ms: 500,
      mature_time_ms: 2000,
      warning_time_ms: 500,
      destroy_time_ms: 300,
    },
    {
      target_id: 4,
      order: 7,
      spawn_delay_ms: 500,
      mature_time_ms: 2000,
      warning_time_ms: 500,
      destroy_time_ms: 300,
    },
  ],
};

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
      isDefault: true,
    },
    create: {
      id: BUBLI_PRESET_ID,
      gameId: BUBLI_GAME_ID,
      name: 'Preset Padrao',
      description: 'Preset inicial padrao do Bubli.',
      isDefault: true,
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

async function seedBestbeat() {
  await prisma.game.upsert({
    where: { id: BESTBEAT_GAME_ID },
    update: {
      name: 'bestbeat',
      description: 'Jogo bestbeat.',
    },
    create: {
      id: BESTBEAT_GAME_ID,
      name: 'bestbeat',
      description: 'Jogo bestbeat.',
    },
  });

  await prisma.preset.upsert({
    where: { id: BESTBEAT_PRESET_ID },
    update: {
      gameId: BESTBEAT_GAME_ID,
      name: 'Default',
      description: 'Preset default: niveis 1 e 2 com config sequence (targets + sequence).',
      isDefault: true,
    },
    create: {
      id: BESTBEAT_PRESET_ID,
      gameId: BESTBEAT_GAME_ID,
      name: 'Default',
      description: 'Preset default: niveis 1 e 2 com config sequence (targets + sequence).',
      isDefault: true,
    },
  });

  await prisma.level.upsert({
    where: { id: BESTBEAT_LEVEL_1_ID },
    update: {
      presetId: BESTBEAT_PRESET_ID,
      name: 'Nivel 1',
      order: 0,
      config: BESTBEAT_LEVEL_1_CONFIG,
    },
    create: {
      id: BESTBEAT_LEVEL_1_ID,
      presetId: BESTBEAT_PRESET_ID,
      name: 'Nivel 1',
      order: 0,
      config: BESTBEAT_LEVEL_1_CONFIG,
    },
  });

  await prisma.level.upsert({
    where: { id: BESTBEAT_LEVEL_2_ID },
    update: {
      presetId: BESTBEAT_PRESET_ID,
      name: 'Nivel 2',
      order: 1,
      config: BESTBEAT_LEVEL_2_CONFIG,
    },
    create: {
      id: BESTBEAT_LEVEL_2_ID,
      presetId: BESTBEAT_PRESET_ID,
      name: 'Nivel 2',
      order: 1,
      config: BESTBEAT_LEVEL_2_CONFIG,
    },
  });
}

async function main() {
  await seedBubli();
  await seedBestbeat();
  console.log('Seed concluido com sucesso.');
  console.log(`BUBLI_GAME_ID=${BUBLI_GAME_ID}`);
  console.log(`BESTBEAT_GAME_ID=${BESTBEAT_GAME_ID}`);
  console.log(`BESTBEAT_PRESET_ID=${BESTBEAT_PRESET_ID}`);
  console.log(`BESTBEAT_LEVEL_1_ID=${BESTBEAT_LEVEL_1_ID}`);
  console.log(`BESTBEAT_LEVEL_2_ID=${BESTBEAT_LEVEL_2_ID}`);
}

main()
  .catch((error) => {
    console.error('Falha ao executar seed:', error);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
