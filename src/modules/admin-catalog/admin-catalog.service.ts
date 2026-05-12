import { Prisma, type PrismaClient } from '@prisma/client';

import { NotFoundError } from '../../shared/errors/not-found-error.js';

type AdminCatalogServiceDeps = {
  prisma: PrismaClient;
};

export function createAdminCatalogService({ prisma }: AdminCatalogServiceDeps) {
  return {
    // Games (admin: all rows, including inactive and soft-deleted)
    async listGames() {
      const games = await prisma.game.findMany({
        orderBy: { name: 'asc' },
        select: {
          id: true,
          name: true,
          description: true,
          isActive: true,
          isDeleted: true,
          createdAt: true,
          updatedAt: true,
        },
      });

      return {
        games: games.map((g) => ({
          id: g.id,
          name: g.name,
          description: g.description,
          is_active: g.isActive,
          is_deleted: g.isDeleted,
          created_at: g.createdAt,
          updated_at: g.updatedAt,
        })),
      };
    },

    async getGame(gameId: string) {
      const game = await prisma.game.findUnique({
        where: { id: gameId },
        select: {
          id: true,
          name: true,
          description: true,
          isActive: true,
          isDeleted: true,
          createdAt: true,
          updatedAt: true,
        },
      });
      if (!game) throw new NotFoundError('Game not found');

      return {
        id: game.id,
        name: game.name,
        description: game.description,
        is_active: game.isActive,
        is_deleted: game.isDeleted,
        created_at: game.createdAt,
        updated_at: game.updatedAt,
      };
    },

    async createGame(input: { name: string; description?: string | null; isActive?: boolean }) {
      const created = await prisma.game.create({
        data: {
          name: input.name,
          description: input.description ?? null,
          isActive: input.isActive ?? true,
          isDeleted: false,
        },
        select: {
          id: true,
          name: true,
          description: true,
          isActive: true,
          isDeleted: true,
          createdAt: true,
          updatedAt: true,
        },
      });

      return {
        id: created.id,
        name: created.name,
        description: created.description,
        is_active: created.isActive,
        is_deleted: created.isDeleted,
        created_at: created.createdAt,
        updated_at: created.updatedAt,
      };
    },

    async updateGame(gameId: string, input: { name?: string; description?: string | null; isActive?: boolean }) {
      const existing = await prisma.game.findUnique({ where: { id: gameId }, select: { id: true } });
      if (!existing) throw new NotFoundError('Game not found');

      const updated = await prisma.game.update({
        where: { id: gameId },
        data: {
          ...(input.name !== undefined ? { name: input.name } : {}),
          ...(input.description !== undefined ? { description: input.description } : {}),
          ...(input.isActive !== undefined ? { isActive: input.isActive } : {}),
        },
        select: {
          id: true,
          name: true,
          description: true,
          isActive: true,
          isDeleted: true,
          createdAt: true,
          updatedAt: true,
        },
      });

      return {
        id: updated.id,
        name: updated.name,
        description: updated.description,
        is_active: updated.isActive,
        is_deleted: updated.isDeleted,
        created_at: updated.createdAt,
        updated_at: updated.updatedAt,
      };
    },

    // Presets
    async listPresets(gameId: string) {
      const game = await prisma.game.findUnique({ where: { id: gameId }, select: { id: true } });
      if (!game) throw new NotFoundError('Game not found');

      const presets = await prisma.preset.findMany({
        where: { gameId },
        orderBy: [{ isDefault: 'desc' }, { name: 'asc' }],
        select: {
          id: true,
          gameId: true,
          name: true,
          description: true,
          isDefault: true,
          isActive: true,
          isDeleted: true,
          createdAt: true,
          updatedAt: true,
        },
      });

      return {
        presets: presets.map((p) => ({
          id: p.id,
          game_id: p.gameId,
          name: p.name,
          description: p.description,
          is_default: p.isDefault,
          is_active: p.isActive,
          is_deleted: p.isDeleted,
          created_at: p.createdAt,
          updated_at: p.updatedAt,
        })),
      };
    },

    async getPreset(presetId: string) {
      const preset = await prisma.preset.findUnique({
        where: { id: presetId },
        select: {
          id: true,
          gameId: true,
          name: true,
          description: true,
          isDefault: true,
          isActive: true,
          isDeleted: true,
          createdAt: true,
          updatedAt: true,
        },
      });
      if (!preset) throw new NotFoundError('Preset not found');

      return {
        id: preset.id,
        game_id: preset.gameId,
        name: preset.name,
        description: preset.description,
        is_default: preset.isDefault,
        is_active: preset.isActive,
        is_deleted: preset.isDeleted,
        created_at: preset.createdAt,
        updated_at: preset.updatedAt,
      };
    },

    async createPreset(input: {
      gameId: string;
      name: string;
      description?: string | null;
      isDefault?: boolean;
      isActive?: boolean;
    }) {
      const game = await prisma.game.findUnique({ where: { id: input.gameId }, select: { id: true } });
      if (!game) throw new NotFoundError('Game not found');

      const created = await prisma.preset.create({
        data: {
          gameId: input.gameId,
          name: input.name,
          description: input.description ?? null,
          isDefault: input.isDefault ?? false,
          isActive: input.isActive ?? true,
          isDeleted: false,
        },
        select: {
          id: true,
          gameId: true,
          name: true,
          description: true,
          isDefault: true,
          isActive: true,
          isDeleted: true,
          createdAt: true,
          updatedAt: true,
        },
      });

      return {
        id: created.id,
        game_id: created.gameId,
        name: created.name,
        description: created.description,
        is_default: created.isDefault,
        is_active: created.isActive,
        is_deleted: created.isDeleted,
        created_at: created.createdAt,
        updated_at: created.updatedAt,
      };
    },

    async updatePreset(
      presetId: string,
      input: { name?: string; description?: string | null; isDefault?: boolean; isActive?: boolean },
    ) {
      const existing = await prisma.preset.findUnique({ where: { id: presetId }, select: { id: true } });
      if (!existing) throw new NotFoundError('Preset not found');

      const updated = await prisma.preset.update({
        where: { id: presetId },
        data: {
          ...(input.name !== undefined ? { name: input.name } : {}),
          ...(input.description !== undefined ? { description: input.description } : {}),
          ...(input.isDefault !== undefined ? { isDefault: input.isDefault } : {}),
          ...(input.isActive !== undefined ? { isActive: input.isActive } : {}),
        },
        select: {
          id: true,
          gameId: true,
          name: true,
          description: true,
          isDefault: true,
          isActive: true,
          isDeleted: true,
          createdAt: true,
          updatedAt: true,
        },
      });

      return {
        id: updated.id,
        game_id: updated.gameId,
        name: updated.name,
        description: updated.description,
        is_default: updated.isDefault,
        is_active: updated.isActive,
        is_deleted: updated.isDeleted,
        created_at: updated.createdAt,
        updated_at: updated.updatedAt,
      };
    },

    async deletePreset(presetId: string) {
      const preset = await prisma.preset.findUnique({
        where: { id: presetId },
        select: { id: true, isDeleted: true },
      });
      if (!preset) throw new NotFoundError('Preset not found');
      if (preset.isDeleted) return;

      await prisma.$transaction(async (tx) => {
        await tx.level.updateMany({
          where: { presetId, isDeleted: false },
          data: { isDeleted: true, isActive: false },
        });
        await tx.preset.update({
          where: { id: presetId },
          data: { isDeleted: true, isActive: false },
        });
      });
    },

    // Levels
    async listLevels(presetId: string) {
      const preset = await prisma.preset.findUnique({ where: { id: presetId }, select: { id: true } });
      if (!preset) throw new NotFoundError('Preset not found');

      const levels = await prisma.level.findMany({
        where: { presetId },
        orderBy: { order: 'asc' },
        select: {
          id: true,
          presetId: true,
          name: true,
          order: true,
          config: true,
          isActive: true,
          isDeleted: true,
          createdAt: true,
          updatedAt: true,
        },
      });

      return {
        levels: levels.map((l) => ({
          id: l.id,
          preset_id: l.presetId,
          name: l.name,
          order: l.order,
          config: l.config,
          is_active: l.isActive,
          is_deleted: l.isDeleted,
          created_at: l.createdAt,
          updated_at: l.updatedAt,
        })),
      };
    },

    async getLevel(levelId: string) {
      const level = await prisma.level.findUnique({
        where: { id: levelId },
        select: {
          id: true,
          presetId: true,
          name: true,
          order: true,
          config: true,
          isActive: true,
          isDeleted: true,
          createdAt: true,
          updatedAt: true,
        },
      });
      if (!level) throw new NotFoundError('Level not found');

      return {
        id: level.id,
        preset_id: level.presetId,
        name: level.name,
        order: level.order,
        config: level.config,
        is_active: level.isActive,
        is_deleted: level.isDeleted,
        created_at: level.createdAt,
        updated_at: level.updatedAt,
      };
    },

    async createLevel(input: {
      presetId: string;
      name: string;
      order: number;
      config: Record<string, unknown>;
      isActive?: boolean;
    }) {
      const preset = await prisma.preset.findUnique({ where: { id: input.presetId }, select: { id: true } });
      if (!preset) throw new NotFoundError('Preset not found');

      const created = await prisma.level.create({
        data: {
          presetId: input.presetId,
          name: input.name,
          order: input.order,
          config: input.config as Prisma.InputJsonValue,
          isActive: input.isActive ?? true,
          isDeleted: false,
        },
        select: {
          id: true,
          presetId: true,
          name: true,
          order: true,
          config: true,
          isActive: true,
          isDeleted: true,
          createdAt: true,
          updatedAt: true,
        },
      });

      return {
        id: created.id,
        preset_id: created.presetId,
        name: created.name,
        order: created.order,
        config: created.config,
        is_active: created.isActive,
        is_deleted: created.isDeleted,
        created_at: created.createdAt,
        updated_at: created.updatedAt,
      };
    },

    async updateLevel(
      levelId: string,
      input: { name?: string; order?: number; config?: Record<string, unknown>; isActive?: boolean },
    ) {
      const existing = await prisma.level.findUnique({ where: { id: levelId }, select: { id: true } });
      if (!existing) throw new NotFoundError('Level not found');

      const updated = await prisma.level.update({
        where: { id: levelId },
        data: {
          ...(input.name !== undefined ? { name: input.name } : {}),
          ...(input.order !== undefined ? { order: input.order } : {}),
          ...(input.config !== undefined ? { config: input.config as Prisma.InputJsonValue } : {}),
          ...(input.isActive !== undefined ? { isActive: input.isActive } : {}),
        },
        select: {
          id: true,
          presetId: true,
          name: true,
          order: true,
          config: true,
          isActive: true,
          isDeleted: true,
          createdAt: true,
          updatedAt: true,
        },
      });

      return {
        id: updated.id,
        preset_id: updated.presetId,
        name: updated.name,
        order: updated.order,
        config: updated.config,
        is_active: updated.isActive,
        is_deleted: updated.isDeleted,
        created_at: updated.createdAt,
        updated_at: updated.updatedAt,
      };
    },

    async deleteLevel(levelId: string) {
      const existing = await prisma.level.findUnique({
        where: { id: levelId },
        select: { id: true, isDeleted: true },
      });
      if (!existing) throw new NotFoundError('Level not found');
      if (existing.isDeleted) return;

      await prisma.level.update({
        where: { id: levelId },
        data: { isDeleted: true, isActive: false },
      });
    },
  };
}

export type AdminCatalogService = ReturnType<typeof createAdminCatalogService>;
