-- At most one "default" preset (isDefault = true) per game
CREATE UNIQUE INDEX "presets_one_default_per_game" ON "presets"("gameId") WHERE "isDefault" = true;
