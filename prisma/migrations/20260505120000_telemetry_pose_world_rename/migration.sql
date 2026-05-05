-- Rename generic telemetry tables (preserve data)
ALTER TABLE "telemetry_landmarks" RENAME TO "telemetry_pose";
ALTER INDEX "telemetry_landmarks_match_id_timestamp_idx" RENAME TO "telemetry_pose_match_id_timestamp_idx";
ALTER TABLE "telemetry_pose" RENAME CONSTRAINT "telemetry_landmarks_pkey" TO "telemetry_pose_pkey";
ALTER TABLE "telemetry_pose" RENAME CONSTRAINT "telemetry_landmarks_match_id_fkey" TO "telemetry_pose_match_id_fkey";

ALTER TABLE "telemetry_input" RENAME TO "telemetry_world";
ALTER INDEX "telemetry_input_match_id_timestamp_idx" RENAME TO "telemetry_world_match_id_timestamp_idx";
ALTER TABLE "telemetry_world" RENAME CONSTRAINT "telemetry_input_pkey" TO "telemetry_world_pkey";
ALTER TABLE "telemetry_world" RENAME CONSTRAINT "telemetry_input_match_id_fkey" TO "telemetry_world_match_id_fkey";

-- trunktilt_pose: landmark_id -> pose_point_id (preserve data)
DROP INDEX IF EXISTS "trunktilt_pose_match_id_frame_id_landmark_id_key";
DROP INDEX IF EXISTS "trunktilt_pose_match_id_landmark_id_timestamp_ms_idx";
ALTER TABLE "trunktilt_pose" RENAME COLUMN "landmark_id" TO "pose_point_id";
CREATE UNIQUE INDEX "trunktilt_pose_match_id_frame_id_pose_point_id_key" ON "trunktilt_pose"("match_id", "frame_id", "pose_point_id");
CREATE INDEX "trunktilt_pose_match_id_pose_point_id_timestamp_ms_idx" ON "trunktilt_pose"("match_id", "pose_point_id", "timestamp_ms");
