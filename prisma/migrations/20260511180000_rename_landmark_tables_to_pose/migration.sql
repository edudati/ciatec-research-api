-- Align bubbles/bestbeat landmark storage with TrunkTilt naming (pose). No data migration beyond rename.
DO $$
BEGIN
  IF to_regclass('public.bubbles_landmarks') IS NOT NULL AND to_regclass('public.bubbles_pose') IS NULL THEN
    ALTER TABLE "bubbles_landmarks" RENAME TO "bubbles_pose";
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.bestbeat_landmarks') IS NOT NULL AND to_regclass('public.bestbeat_pose') IS NULL THEN
    ALTER TABLE "bestbeat_landmarks" RENAME TO "bestbeat_pose";
  END IF;
END $$;
