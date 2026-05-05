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
/** RFC 4122 variant: 4th group must start with 8, 9, a, or b (Zod .uuid() is strict) */
export const BESTBEAT_LEVEL_1_ID = '0a23e6c8-3d4f-4a5b-8b1a-2e3f4a5b6c7d';
export const BESTBEAT_LEVEL_2_ID = '1b34f7d9-4e5a-4b6c-8d1e-2f3a4b5c6d7e';

/** TrunkTilt — IDs fixos (variant RFC 4122 para Zod .uuid() estrito). */
export const TRUNKTILT_GAME_ID = 'a1b2c3d4-e5f6-4789-a8b0-c1d2e3f4a5b6';
export const TRUNKTILT_PRESET_ID = 'b2c3d4e5-f6a7-4890-b9c1-d2e3f4a5b6c7';
export const TRUNKTILT_LEVEL_1_ID = 'c3d4e5f6-a7b8-4901-8c9d-e3f4a5b6c7d8';
export const TRUNKTILT_LEVEL_2_ID = 'd4e5f6a7-b8c9-4123-91e3-f4a5b6c7d8e9';
export const TRUNKTILT_LEVEL_3_ID = 'e5f6a7b8-c9d0-4234-a2f4-a5b6c7d8e9f0';

/** Níveis TrunkTilt: JSON embutido no seed. */
const TRUNKTILT_LEVEL_1_DOC = {
    "levelName": "Fase 1 — Tutorial",
    "cellSize": 1.0,
    "grid": [
        {
            "row": [0,0,0,0,0,6,0,0,0,0,0,0],
        },
        {
            "row": [0,0,0,0,0,1,0,0,0,0,0,0],
        },
        {
            "row": [0,0,0,0,0,1,0,0,0,0,0,0],
        },
        {
            "row": [0,0,0,0,0,1,0,0,0,0,0,0],
        },
        {
            "row": [0,0,0,0,0,3,0,0,0,0,0,0],
        },
        {
            "row": [0,0,0,0,0,1,0,0,0,0,0,0],
        },
        {
            "row": [0,0,0,0,0,1,1,1,1,0,0,0],
        },
        {
            "row": [0,0,0,0,0,0,0,0,1,0,0,0],
        },
        {
            "row": [0,0,0,0,0,0,0,0,5,0,0,0],
        },
        {
            "row": [0,0,0,0,0,0,0,0,1,0,0,0],
        },
        {
            "row": [0,0,0,0,0,0,0,0,1,0,0,0],
        },
        {
            "row": [0,0,0,0,0,0,0,0,1,5,2,0],
        },
        {
            "row": [0,0,0,0,0,0,0,0,2,0,0,0],
        },
        {
            "row": [0,0,0,0,0,0,0,0,2,0,0,0],
        },
        {
            "row": [0,0,0,0,0,0,0,0,4,0,0,0],
        },
        {
            "row": [0,0,0,0,0,0,0,0,3,0,0,0],
        },
        {
            "row": [0,0,0,0,0,0,0,0,1,0,0,0],
        },
        {
            "row": [0,0,0,0,0,0,0,0,7,0,0,0],
        },
    ],
    "details": [
        {
            "tileId": 3,
            "frequency": 1.0,
            "amplitude": 3.0,
            "coinValue": 0,
            "elevation": 0.0,
            "x": 5,
            "y": 4
        },
        {
            "tileId": 5,
            "frequency": 0,
            "amplitude": 0,
            "coinValue": 50,
            "elevation": 0.0,
            "x": 8,
            "y": 8
        },
        {
            "tileId": 2,
            "frequency": 0,
            "amplitude": 0,
            "coinValue": 0,
            "elevation": 0.0,
            "x": 10,
            "y": 11
        }
    ]
} as const;
const TRUNKTILT_LEVEL_2_DOC = {
    "levelName": "Fase 2 — A Subida",
    "cellSize": 1.0,
    "grid": [
        {
            "row": [0,0,0,0,1,1,1,6,0,0],
        },
        {
            "row": [0,0,0,0,5,0,0,0,0,0],
        },
        {
            "row": [0,0,0,0,8,0,0,0,0,0],
        },
        {
            "row": [0,0,0,0,1,0,0,0,0,0],
        },
        {
            "row": [0,0,0,0,3,0,0,0,0,0],
        },
        {
            "row": [0,0,0,0,1,1,1,0,0,0],
        },
        {
            "row": [0,0,0,0,0,0,1,0,0,0],
        },
        {
            "row": [0,0,0,0,1,1,1,0,0,0],
        },
        {
            "row": [0,0,0,0,9,0,0,0,0,0],
        },
        {
            "row": [0,0,0,0,0,0,0,0,0,0],
        },
        {
            "row": [0,0,0,0,1,0,0,0,0,0],
        },
        {
            "row": [0,0,0,0,7,0,0,0,0,0],
        }
    ],
    "details": [
        {
            "tileId": 8,
            "rampDirection": "North",
            "elevation": 0.0,
            "targetElevation": 1.5,
            "frequency": 0,
            "amplitude": 0,
            "coinValue": 0
        },
        {
            "tileId": 9,
            "rampDirection": "North",
            "elevation": 1.5,
            "targetElevation": 0.0,
            "frequency": 0,
            "amplitude": 0,
            "coinValue": 0
        },
        {
            "tileId": 1,
            "frequency": 0,
            "amplitude": 0,
            "coinValue": 0
        },
        {
            "tileId": 2,
            "frequency": 0,
            "amplitude": 0,
            "coinValue": 0
        },
        {
            "tileId": 3,
            "frequency": 2.0,
            "amplitude": 1.5,
            "coinValue": 0
        },
        {
            "tileId": 5,
            "frequency": 0,
            "amplitude": 0,
            "coinValue": 25
        },
        {
            "tileId": 7,
            "frequency": 0,
            "amplitude": 0,
            "coinValue": 0
        }
    ]
} as const;
const TRUNKTILT_LEVEL_3_DOC = {
  "levelName": "Arena Circuit 1",
  "cellSize": 1.0,
  "grid": [
    {
      "row": [2,2,2,2,1,1,1,1,1,1],
    },
    {
      "row": [2,5,1,5,1,5,2,2,2,1],
    },
    {
      "row": [2,5,1,5,1,5,2,5,5,1],
    },
    {
      "row": [2,1,1,1,1,5,2,1,1,1],
    },
    {
      "row": [2,6,1,1,1,5,2,4,3,1],
    },
    {
      "row": [2,1,1,1,1,5,2,1,1,1],
    },
    {
      "row": [2,5,1,5,1,5,2,5,5,1],
    },
    {
      "row": [2,5,1,5,1,5,2,2,2,1],
    },
    {
      "row": [2,2,2,2,1,1,1,1,1,1],
    }
  ],
  "details": []
} as const;

const TRUNKTILT_SEED_LEVEL_1 = {
  name: TRUNKTILT_LEVEL_1_DOC.levelName,
  config: TRUNKTILT_LEVEL_1_DOC as Prisma.InputJsonValue,
};
const TRUNKTILT_SEED_LEVEL_2 = {
  name: TRUNKTILT_LEVEL_2_DOC.levelName,
  config: TRUNKTILT_LEVEL_2_DOC as Prisma.InputJsonValue,
};
const TRUNKTILT_SEED_LEVEL_3 = {
  name: TRUNKTILT_LEVEL_3_DOC.levelName,
  config: TRUNKTILT_LEVEL_3_DOC as Prisma.InputJsonValue,
};

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

  // `order` por preset: bestbeat usa 0, 1, ... (Bubli acima usa 1, 2, 3 — ambos validos).
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

async function seedTrunktilt() {
  await prisma.game.upsert({
    where: { id: TRUNKTILT_GAME_ID },
    update: {
      name: 'trunktilt',
      description: 'TrunkTilt — tres niveis (config embutido neste seed).',
    },
    create: {
      id: TRUNKTILT_GAME_ID,
      name: 'trunktilt',
      description: 'TrunkTilt — tres niveis (config embutido neste seed).',
    },
  });

  await prisma.preset.upsert({
    where: { id: TRUNKTILT_PRESET_ID },
    update: {
      gameId: TRUNKTILT_GAME_ID,
      name: 'Default',
      description: 'Preset default TrunkTilt: tres fases.',
      isDefault: true,
    },
    create: {
      id: TRUNKTILT_PRESET_ID,
      gameId: TRUNKTILT_GAME_ID,
      name: 'Default',
      description: 'Preset default TrunkTilt: tres fases.',
      isDefault: true,
    },
  });

  await prisma.level.upsert({
    where: { id: TRUNKTILT_LEVEL_1_ID },
    update: {
      presetId: TRUNKTILT_PRESET_ID,
      name: TRUNKTILT_SEED_LEVEL_1.name,
      order: 0,
      config: TRUNKTILT_SEED_LEVEL_1.config,
    },
    create: {
      id: TRUNKTILT_LEVEL_1_ID,
      presetId: TRUNKTILT_PRESET_ID,
      name: TRUNKTILT_SEED_LEVEL_1.name,
      order: 0,
      config: TRUNKTILT_SEED_LEVEL_1.config,
    },
  });

  await prisma.level.upsert({
    where: { id: TRUNKTILT_LEVEL_2_ID },
    update: {
      presetId: TRUNKTILT_PRESET_ID,
      name: TRUNKTILT_SEED_LEVEL_2.name,
      order: 1,
      config: TRUNKTILT_SEED_LEVEL_2.config,
    },
    create: {
      id: TRUNKTILT_LEVEL_2_ID,
      presetId: TRUNKTILT_PRESET_ID,
      name: TRUNKTILT_SEED_LEVEL_2.name,
      order: 1,
      config: TRUNKTILT_SEED_LEVEL_2.config,
    },
  });

  await prisma.level.upsert({
    where: { id: TRUNKTILT_LEVEL_3_ID },
    update: {
      presetId: TRUNKTILT_PRESET_ID,
      name: TRUNKTILT_SEED_LEVEL_3.name,
      order: 2,
      config: TRUNKTILT_SEED_LEVEL_3.config,
    },
    create: {
      id: TRUNKTILT_LEVEL_3_ID,
      presetId: TRUNKTILT_PRESET_ID,
      name: TRUNKTILT_SEED_LEVEL_3.name,
      order: 2,
      config: TRUNKTILT_SEED_LEVEL_3.config,
    },
  });
}

async function main() {
  await seedBubli();
  await seedBestbeat();
  await seedTrunktilt();
  console.log('Seed concluido com sucesso.');
  console.log(`BUBLI_GAME_ID=${BUBLI_GAME_ID}`);
  console.log(`BESTBEAT_GAME_ID=${BESTBEAT_GAME_ID}`);
  console.log(`BESTBEAT_PRESET_ID=${BESTBEAT_PRESET_ID}`);
  console.log(`BESTBEAT_LEVEL_1_ID=${BESTBEAT_LEVEL_1_ID}`);
  console.log(`BESTBEAT_LEVEL_2_ID=${BESTBEAT_LEVEL_2_ID}`);
  console.log(`TRUNKTILT_GAME_ID=${TRUNKTILT_GAME_ID}`);
  console.log(`TRUNKTILT_PRESET_ID=${TRUNKTILT_PRESET_ID}`);
  console.log(`TRUNKTILT_LEVEL_1_ID=${TRUNKTILT_LEVEL_1_ID}`);
  console.log(`TRUNKTILT_LEVEL_2_ID=${TRUNKTILT_LEVEL_2_ID}`);
  console.log(`TRUNKTILT_LEVEL_3_ID=${TRUNKTILT_LEVEL_3_ID}`);
}

main()
  .catch((error) => {
    console.error('Falha ao executar seed:', error);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
