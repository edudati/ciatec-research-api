-- AlterTable
ALTER TABLE "match_results" ADD COLUMN "idempotency_key" TEXT;

-- CreateIndex
CREATE UNIQUE INDEX "match_results_idempotency_key_key" ON "match_results"("idempotency_key");
