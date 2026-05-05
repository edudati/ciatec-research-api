-- Alter timestamps de eventos/telemetria para epoch em milissegundos
ALTER TABLE "match_events"
  ALTER COLUMN "timestamp" TYPE BIGINT
  USING (EXTRACT(EPOCH FROM "timestamp") * 1000)::BIGINT;

ALTER TABLE "telemetry_landmarks"
  ALTER COLUMN "timestamp" TYPE BIGINT
  USING (EXTRACT(EPOCH FROM "timestamp") * 1000)::BIGINT;

ALTER TABLE "telemetry_input"
  ALTER COLUMN "timestamp" TYPE BIGINT
  USING (EXTRACT(EPOCH FROM "timestamp") * 1000)::BIGINT;
