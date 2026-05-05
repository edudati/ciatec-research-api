-- AlterTable
ALTER TABLE "sessions" ALTER COLUMN "session_date" DROP DEFAULT;

-- CreateTable
CREATE TABLE "user_level_progress" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "levelId" TEXT NOT NULL,
    "unlocked" BOOLEAN NOT NULL DEFAULT false,
    "completed" BOOLEAN NOT NULL DEFAULT false,
    "bests" JSONB NOT NULL DEFAULT '{}',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "user_level_progress_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "user_level_progress_userId_idx" ON "user_level_progress"("userId");

-- CreateIndex
CREATE INDEX "user_level_progress_levelId_idx" ON "user_level_progress"("levelId");

-- CreateIndex
CREATE UNIQUE INDEX "user_level_progress_userId_levelId_key" ON "user_level_progress"("userId", "levelId");

-- AddForeignKey
ALTER TABLE "user_level_progress" ADD CONSTRAINT "user_level_progress_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "user_level_progress" ADD CONSTRAINT "user_level_progress_levelId_fkey" FOREIGN KEY ("levelId") REFERENCES "levels"("id") ON DELETE CASCADE ON UPDATE CASCADE;
