-- AlterTable
ALTER TABLE "presets" ADD COLUMN     "isDefault" BOOLEAN NOT NULL DEFAULT false;

-- CreateIndex
CREATE INDEX "presets_gameId_isDefault_idx" ON "presets"("gameId", "isDefault");
