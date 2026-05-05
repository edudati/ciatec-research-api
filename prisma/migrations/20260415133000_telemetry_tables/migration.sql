-- CreateTable
CREATE TABLE "telemetry_landmarks" (
    "id" TEXT NOT NULL,
    "match_id" TEXT NOT NULL,
    "timestamp" TIMESTAMP(3) NOT NULL,
    "data" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "telemetry_landmarks_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "telemetry_input" (
    "id" TEXT NOT NULL,
    "match_id" TEXT NOT NULL,
    "timestamp" TIMESTAMP(3) NOT NULL,
    "device" TEXT NOT NULL,
    "data" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "telemetry_input_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "telemetry_landmarks_match_id_timestamp_idx" ON "telemetry_landmarks"("match_id", "timestamp");

-- CreateIndex
CREATE INDEX "telemetry_input_match_id_timestamp_idx" ON "telemetry_input"("match_id", "timestamp");

-- AddForeignKey
ALTER TABLE "telemetry_landmarks" ADD CONSTRAINT "telemetry_landmarks_match_id_fkey" FOREIGN KEY ("match_id") REFERENCES "matches"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "telemetry_input" ADD CONSTRAINT "telemetry_input_match_id_fkey" FOREIGN KEY ("match_id") REFERENCES "matches"("id") ON DELETE CASCADE ON UPDATE CASCADE;
