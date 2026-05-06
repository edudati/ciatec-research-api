-- Remove generic gameplay telemetry (dados antigos descartados — re-seed se necessário)
DROP TABLE IF EXISTS "match_events" CASCADE;
DROP TABLE IF EXISTS "telemetry_landmarks" CASCADE;
DROP TABLE IF EXISTS "telemetry_world" CASCADE;

-- bubbles — tabelas isoladas
CREATE TABLE "bubbles_events" (
    "id" TEXT NOT NULL,
    "match_id" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "timestamp" BIGINT NOT NULL,
    "data" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "bubbles_events_pkey" PRIMARY KEY ("id")
);
CREATE INDEX "bubbles_events_match_id_timestamp_idx" ON "bubbles_events"("match_id", "timestamp");
ALTER TABLE "bubbles_events" ADD CONSTRAINT "bubbles_events_match_id_fkey" FOREIGN KEY ("match_id") REFERENCES "matches"("id") ON DELETE CASCADE ON UPDATE CASCADE;

CREATE TABLE "bubbles_landmarks" (
    "id" TEXT NOT NULL,
    "match_id" TEXT NOT NULL,
    "timestamp" BIGINT NOT NULL,
    "data" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "bubbles_landmarks_pkey" PRIMARY KEY ("id")
);
CREATE INDEX "bubbles_landmarks_match_id_timestamp_idx" ON "bubbles_landmarks"("match_id", "timestamp");
ALTER TABLE "bubbles_landmarks" ADD CONSTRAINT "bubbles_landmarks_match_id_fkey" FOREIGN KEY ("match_id") REFERENCES "matches"("id") ON DELETE CASCADE ON UPDATE CASCADE;

CREATE TABLE "bubbles_world" (
    "id" TEXT NOT NULL,
    "match_id" TEXT NOT NULL,
    "timestamp" BIGINT NOT NULL,
    "device" TEXT NOT NULL,
    "data" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "bubbles_world_pkey" PRIMARY KEY ("id")
);
CREATE INDEX "bubbles_world_match_id_timestamp_idx" ON "bubbles_world"("match_id", "timestamp");
ALTER TABLE "bubbles_world" ADD CONSTRAINT "bubbles_world_match_id_fkey" FOREIGN KEY ("match_id") REFERENCES "matches"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- bestbeat — tabelas isoladas
CREATE TABLE "bestbeat_events" (
    "id" TEXT NOT NULL,
    "match_id" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "timestamp" BIGINT NOT NULL,
    "data" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "bestbeat_events_pkey" PRIMARY KEY ("id")
);
CREATE INDEX "bestbeat_events_match_id_timestamp_idx" ON "bestbeat_events"("match_id", "timestamp");
ALTER TABLE "bestbeat_events" ADD CONSTRAINT "bestbeat_events_match_id_fkey" FOREIGN KEY ("match_id") REFERENCES "matches"("id") ON DELETE CASCADE ON UPDATE CASCADE;

CREATE TABLE "bestbeat_landmarks" (
    "id" TEXT NOT NULL,
    "match_id" TEXT NOT NULL,
    "timestamp" BIGINT NOT NULL,
    "data" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "bestbeat_landmarks_pkey" PRIMARY KEY ("id")
);
CREATE INDEX "bestbeat_landmarks_match_id_timestamp_idx" ON "bestbeat_landmarks"("match_id", "timestamp");
ALTER TABLE "bestbeat_landmarks" ADD CONSTRAINT "bestbeat_landmarks_match_id_fkey" FOREIGN KEY ("match_id") REFERENCES "matches"("id") ON DELETE CASCADE ON UPDATE CASCADE;

CREATE TABLE "bestbeat_world" (
    "id" TEXT NOT NULL,
    "match_id" TEXT NOT NULL,
    "timestamp" BIGINT NOT NULL,
    "device" TEXT NOT NULL,
    "data" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "bestbeat_world_pkey" PRIMARY KEY ("id")
);
CREATE INDEX "bestbeat_world_match_id_timestamp_idx" ON "bestbeat_world"("match_id", "timestamp");
ALTER TABLE "bestbeat_world" ADD CONSTRAINT "bestbeat_world_match_id_fkey" FOREIGN KEY ("match_id") REFERENCES "matches"("id") ON DELETE CASCADE ON UPDATE CASCADE;
