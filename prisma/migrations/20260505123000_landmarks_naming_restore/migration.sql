-- Generic articulations JSON: telemetry_pose -> telemetry_landmarks
ALTER TABLE "telemetry_pose" RENAME TO "telemetry_landmarks";
ALTER INDEX "telemetry_pose_match_id_timestamp_idx" RENAME TO "telemetry_landmarks_match_id_timestamp_idx";
ALTER TABLE "telemetry_landmarks" RENAME CONSTRAINT "telemetry_pose_pkey" TO "telemetry_landmarks_pkey";
ALTER TABLE "telemetry_landmarks" RENAME CONSTRAINT "telemetry_pose_match_id_fkey" TO "telemetry_landmarks_match_id_fkey";

-- TrunkTilt typed pose rows: pose_point_id -> landmark_id (MediaPipe landmark index)
DROP INDEX IF EXISTS "trunktilt_pose_match_id_frame_id_pose_point_id_key";
DROP INDEX IF EXISTS "trunktilt_pose_match_id_pose_point_id_timestamp_ms_idx";
ALTER TABLE "trunktilt_pose" RENAME COLUMN "pose_point_id" TO "landmark_id";
CREATE UNIQUE INDEX "trunktilt_pose_match_id_frame_id_landmark_id_key" ON "trunktilt_pose"("match_id", "frame_id", "landmark_id");
CREATE INDEX "trunktilt_pose_match_id_landmark_id_timestamp_ms_idx" ON "trunktilt_pose"("match_id", "landmark_id", "timestamp_ms");
