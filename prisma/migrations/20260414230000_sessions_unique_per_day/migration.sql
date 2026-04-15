-- AlterTable
ALTER TABLE "sessions"
ADD COLUMN "session_date" DATE NOT NULL DEFAULT CURRENT_DATE;

-- CreateIndex
CREATE UNIQUE INDEX "sessions_userId_session_date_key" ON "sessions"("userId", "session_date");
