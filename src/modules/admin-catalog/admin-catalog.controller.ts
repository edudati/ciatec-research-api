import type { FastifyReply, FastifyRequest } from 'fastify';

import type { AdminCatalogService } from './admin-catalog.service.js';
import {
  createGameBodySchema,
  createLevelBodySchema,
  createPresetBodySchema,
  gameIdParamsSchema,
  levelIdParamsSchema,
  presetIdParamsSchema,
  updateGameBodySchema,
  updateLevelBodySchema,
  updatePresetBodySchema,
} from '../catalog/catalog.schema.js';

export function createAdminCatalogController(service: AdminCatalogService) {
  return {
    // Games
    async listGames(_request: FastifyRequest, reply: FastifyReply) {
      const result = await service.listGames();
      return reply.send(result);
    },

    async getGame(request: FastifyRequest, reply: FastifyReply) {
      const params = gameIdParamsSchema.parse(request.params);
      const result = await service.getGame(params.game_id);
      return reply.send(result);
    },

    async createGame(request: FastifyRequest, reply: FastifyReply) {
      const body = createGameBodySchema.parse(request.body);
      const result = await service.createGame({
        name: body.name,
        description: body.description,
        isActive: body.is_active,
      });
      return reply.status(201).send(result);
    },

    async updateGame(request: FastifyRequest, reply: FastifyReply) {
      const params = gameIdParamsSchema.parse(request.params);
      const body = updateGameBodySchema.parse(request.body);
      const result = await service.updateGame(params.game_id, {
        name: body.name,
        description: body.description,
        isActive: body.is_active,
      });
      return reply.send(result);
    },

    async listPresets(request: FastifyRequest, reply: FastifyReply) {
      const params = gameIdParamsSchema.parse(request.params);
      const result = await service.listPresets(params.game_id);
      return reply.send(result);
    },

    // Presets
    async getPreset(request: FastifyRequest, reply: FastifyReply) {
      const params = presetIdParamsSchema.parse(request.params);
      const result = await service.getPreset(params.preset_id);
      return reply.send(result);
    },

    async createPreset(request: FastifyRequest, reply: FastifyReply) {
      const body = createPresetBodySchema.parse(request.body);
      const result = await service.createPreset({
        gameId: body.game_id,
        name: body.name,
        description: body.description,
        isDefault: body.is_default,
        isActive: body.is_active,
      });
      return reply.status(201).send(result);
    },

    async updatePreset(request: FastifyRequest, reply: FastifyReply) {
      const params = presetIdParamsSchema.parse(request.params);
      const body = updatePresetBodySchema.parse(request.body);
      const result = await service.updatePreset(params.preset_id, {
        name: body.name,
        description: body.description,
        isDefault: body.is_default,
        isActive: body.is_active,
      });
      return reply.send(result);
    },

    async deletePreset(request: FastifyRequest, reply: FastifyReply) {
      const params = presetIdParamsSchema.parse(request.params);
      await service.deletePreset(params.preset_id);
      return reply.status(204).send();
    },

    // Levels
    async listLevels(request: FastifyRequest, reply: FastifyReply) {
      const params = presetIdParamsSchema.parse(request.params);
      const result = await service.listLevels(params.preset_id);
      return reply.send(result);
    },

    async getLevel(request: FastifyRequest, reply: FastifyReply) {
      const params = levelIdParamsSchema.parse(request.params);
      const result = await service.getLevel(params.level_id);
      return reply.send(result);
    },

    async createLevel(request: FastifyRequest, reply: FastifyReply) {
      const body = createLevelBodySchema.parse(request.body);
      const result = await service.createLevel({
        presetId: body.preset_id,
        name: body.name,
        order: body.order,
        config: body.config,
        isActive: body.is_active,
      });
      return reply.status(201).send(result);
    },

    async updateLevel(request: FastifyRequest, reply: FastifyReply) {
      const params = levelIdParamsSchema.parse(request.params);
      const body = updateLevelBodySchema.parse(request.body);
      const result = await service.updateLevel(params.level_id, {
        name: body.name,
        order: body.order,
        config: body.config,
        isActive: body.is_active,
      });
      return reply.send(result);
    },

    async deleteLevel(request: FastifyRequest, reply: FastifyReply) {
      const params = levelIdParamsSchema.parse(request.params);
      await service.deleteLevel(params.level_id);
      return reply.status(204).send();
    },
  };
}

