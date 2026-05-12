-- Align bubbles/bestbeat landmark storage with TrunkTilt naming (pose). No data migration beyond rename.

-- ── bubbles_landmarks → bubbles_pose ──
DO $$
BEGIN
  IF to_regclass('public.bubbles_landmarks') IS NOT NULL AND to_regclass('public.bubbles_pose') IS NULL THEN
    ALTER TABLE "bubbles_landmarks" RENAME TO "bubbles_pose";
    ALTER TABLE "bubbles_pose" RENAME CONSTRAINT "bubbles_landmarks_pkey" TO "bubbles_pose_pkey";
    ALTER TABLE "bubbles_pose" RENAME CONSTRAINT "bubbles_landmarks_match_id_fkey" TO "bubbles_pose_match_id_fkey";
    ALTER INDEX "bubbles_landmarks_match_id_timestamp_idx" RENAME TO "bubbles_pose_match_id_timestamp_idx";
  END IF;
END $$;

-- ── bestbeat_landmarks → bestbeat_pose ──
DO $$
BEGIN
  IF to_regclass('public.bestbeat_landmarks') IS NOT NULL AND to_regclass('public.bestbeat_pose') IS NULL THEN
    ALTER TABLE "bestbeat_landmarks" RENAME TO "bestbeat_pose";
    ALTER TABLE "bestbeat_pose" RENAME CONSTRAINT "bestbeat_landmarks_pkey" TO "bestbeat_pose_pkey";
    ALTER TABLE "bestbeat_pose" RENAME CONSTRAINT "bestbeat_landmarks_match_id_fkey" TO "bestbeat_pose_match_id_fkey";
    ALTER INDEX "bestbeat_landmarks_match_id_timestamp_idx" RENAME TO "bestbeat_pose_match_id_timestamp_idx";
  END IF;
END $$;
