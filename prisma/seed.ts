import 'dotenv/config';

import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { PrismaPg } from '@prisma/adapter-pg';
import { Prisma, PrismaClient } from '@prisma/client';

import {
  BESTBEAT_GAME_ID,
  BUBBLES_GAME_ID,
  TRUNCKTILT_GAME_ID,
} from '../src/constants/game-ids.js';

const seedFileDir = dirname(fileURLToPath(import.meta.url));

function loadTrunktiltLevelJson(fileName: string): Prisma.InputJsonValue {
  const filePath = join(seedFileDir, '..', 'docs', 'trunktilt', fileName);
  const raw = readFileSync(filePath, 'utf8');
  return JSON.parse(raw) as Prisma.InputJsonValue;
}

function levelNameFromConfig(config: Prisma.InputJsonValue, fallback: string): string {
  if (
    typeof config === 'object' &&
    config !== null &&
    'levelName' in config &&
    typeof (config as { levelName: unknown }).levelName === 'string'
  ) {
    return (config as { levelName: string }).levelName;
  }
  return fallback;
}

if (!process.env.DATABASE_URL) {
  throw new Error('DATABASE_URL nao definida para executar seed.');
}

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL });
const prisma = new PrismaClient({ adapter });

export { BUBBLES_GAME_ID, BESTBEAT_GAME_ID, TRUNCKTILT_GAME_ID };

/** Compat: mesmo UUID que `BUBBLES_GAME_ID` (antigo nome Bubli). */
export const BUBLI_GAME_ID = BUBBLES_GAME_ID;

export const BUBBLES_PRESET_ID = '0ed90aca-1200-4781-b11f-0368ca417b17';
export const BUBBLES_LEVEL_1_ID = 'c7476ec4-2bc5-4fee-afde-648e82fef278';
export const BUBBLES_LEVEL_2_ID = 'bcb50b2d-769a-4a52-82f7-9dda7f52adf3';
export const BUBBLES_LEVEL_3_ID = 'ee5bfb25-4f6f-4355-a050-ece42e0dc9ac';

/** Compat: mesmos UUIDs que `BUBBLES_LEVEL_*`. */
export const BUBLI_LEVEL_1_ID = BUBBLES_LEVEL_1_ID;
export const BUBLI_LEVEL_2_ID = BUBBLES_LEVEL_2_ID;
export const BUBLI_LEVEL_3_ID = BUBBLES_LEVEL_3_ID;
export const BUBLI_PRESET_ID = BUBBLES_PRESET_ID;

/** Bestbeat — IDs fixos para o cliente e documentação. */
export const BESTBEAT_PRESET_ID = 'f912d5b7-2c3e-4f4a-9b0a-1d2e3f4a5b6c';
/** RFC 4122 variant: 4th group must start with 8, 9, a, or b (Zod .uuid() is strict) */
export const BESTBEAT_LEVEL_1_ID = '0a23e6c8-3d4f-4a5b-8b1a-2e3f4a5b6c7d';
export const BESTBEAT_LEVEL_2_ID = '1b34f7d9-4e5a-4b6c-8d1e-2f3a4b5c6d7e';

/** TrunkTilt — preset default + níveis (UUIDs válidos para validação Zod .uuid()). */
export const TRUNCKTILT_PRESET_ID = 'c2d4e6f8-1a3b-4c8d-9e2f-4a6b8c0d2e4f';
export const TRUNCKTILT_LEVEL_1_ID = 'd3e5f7a9-2b4c-4d9e-af3b-5b7c9d1e3f5a';
export const TRUNCKTILT_LEVEL_2_ID = 'e4f6a8b0-3c5d-4e0f-b04c-6c8d0e2f4a6b';
export const TRUNCKTILT_LEVEL_3_ID = 'f5a7b9c1-4d6e-4f1a-815d-7d9e1f3a5b7c';

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

async function seedBubbles() {
  await prisma.game.upsert({
    where: { id: BUBBLES_GAME_ID },
    update: {
      name: 'bubbles',
      description: 'Jogo bubbles.',
    },
    create: {
      id: BUBBLES_GAME_ID,
      name: 'bubbles',
      description: 'Jogo bubbles.',
    },
  });

  await prisma.preset.upsert({
    where: { id: BUBBLES_PRESET_ID },
    update: {
      gameId: BUBBLES_GAME_ID,
      name: 'Preset Padrao',
      description: 'Preset inicial padrao do bubbles.',
      isDefault: true,
    },
    create: {
      id: BUBBLES_PRESET_ID,
      gameId: BUBBLES_GAME_ID,
      name: 'Preset Padrao',
      description: 'Preset inicial padrao do bubbles.',
      isDefault: true,
    },
  });

  await prisma.level.upsert({
    where: { id: BUBBLES_LEVEL_1_ID },
    update: {
      presetId: BUBBLES_PRESET_ID,
      name: 'Nivel 1',
      order: 1,
      config: {},
    },
    create: {
      id: BUBBLES_LEVEL_1_ID,
      presetId: BUBBLES_PRESET_ID,
      name: 'Nivel 1',
      order: 1,
      config: {},
    },
  });

  await prisma.level.upsert({
    where: { id: BUBBLES_LEVEL_2_ID },
    update: {
      presetId: BUBBLES_PRESET_ID,
      name: 'Nivel 2',
      order: 2,
      config: {},
    },
    create: {
      id: BUBBLES_LEVEL_2_ID,
      presetId: BUBBLES_PRESET_ID,
      name: 'Nivel 2',
      order: 2,
      config: {},
    },
  });

  await prisma.level.upsert({
    where: { id: BUBBLES_LEVEL_3_ID },
    update: {
      presetId: BUBBLES_PRESET_ID,
      name: 'Nivel 3',
      order: 3,
      config: {},
    },
    create: {
      id: BUBBLES_LEVEL_3_ID,
      presetId: BUBBLES_PRESET_ID,
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

async function seedTruncktilt() {
  await prisma.game.upsert({
    where: { id: TRUNCKTILT_GAME_ID },
    update: {
      name: 'truncktilt',
      description: 'Jogo truncktilt.',
    },
    create: {
      id: TRUNCKTILT_GAME_ID,
      name: 'truncktilt',
      description: 'Jogo truncktilt.',
    },
  });

  await prisma.preset.upsert({
    where: { id: TRUNCKTILT_PRESET_ID },
    update: {
      gameId: TRUNCKTILT_GAME_ID,
      name: 'Default',
      description: 'Preset default TrunkTilt: tres fases (MapGridData em docs/trunktilt).',
      isDefault: true,
    },
    create: {
      id: TRUNCKTILT_PRESET_ID,
      gameId: TRUNCKTILT_GAME_ID,
      name: 'Default',
      description: 'Preset default TrunkTilt: tres fases (MapGridData em docs/trunktilt).',
      isDefault: true,
    },
  });

  const trunktiltLevels: ReadonlyArray<{
    id: string;
    file: string;
    order: number;
    fallbackName: string;
  }> = [
    { id: TRUNCKTILT_LEVEL_1_ID, file: 'level_01.json', order: 0, fallbackName: 'Nivel 1' },
    { id: TRUNCKTILT_LEVEL_2_ID, file: 'level_02.json', order: 1, fallbackName: 'Nivel 2' },
    { id: TRUNCKTILT_LEVEL_3_ID, file: 'level_03.json', order: 2, fallbackName: 'Nivel 3' },
  ];

  for (const { id, file, order, fallbackName } of trunktiltLevels) {
    const config = loadTrunktiltLevelJson(file);
    const name = levelNameFromConfig(config, fallbackName);

    await prisma.level.upsert({
      where: { id },
      update: {
        presetId: TRUNCKTILT_PRESET_ID,
        name,
        order,
        config,
      },
      create: {
        id,
        presetId: TRUNCKTILT_PRESET_ID,
        name,
        order,
        config,
      },
    });
  }
}

async function main() {
  await seedBubbles();
  await seedBestbeat();
  await seedTruncktilt();
  console.log('Seed concluido com sucesso.');
  console.log(`BUBBLES_GAME_ID=${BUBBLES_GAME_ID}`);
  console.log(`BESTBEAT_GAME_ID=${BESTBEAT_GAME_ID}`);
  console.log(`BESTBEAT_PRESET_ID=${BESTBEAT_PRESET_ID}`);
  console.log(`BESTBEAT_LEVEL_1_ID=${BESTBEAT_LEVEL_1_ID}`);
  console.log(`BESTBEAT_LEVEL_2_ID=${BESTBEAT_LEVEL_2_ID}`);
  console.log(`TRUNCKTILT_GAME_ID=${TRUNCKTILT_GAME_ID}`);
  console.log(`TRUNCKTILT_PRESET_ID=${TRUNCKTILT_PRESET_ID}`);
  console.log(`TRUNCKTILT_LEVEL_1_ID=${TRUNCKTILT_LEVEL_1_ID}`);
  console.log(`TRUNCKTILT_LEVEL_2_ID=${TRUNCKTILT_LEVEL_2_ID}`);
  console.log(`TRUNCKTILT_LEVEL_3_ID=${TRUNCKTILT_LEVEL_3_ID}`);
}

main()
  .catch((error) => {
    console.error('Falha ao executar seed:', error);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
