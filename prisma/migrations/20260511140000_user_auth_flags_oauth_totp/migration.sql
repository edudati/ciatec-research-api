-- AlterTable: onboarding + email verification + TOTP groundwork (idempotent for partial retries)
DO $$
BEGIN
  ALTER TABLE "users" ADD COLUMN "is_first_access" BOOLEAN NOT NULL DEFAULT true;
EXCEPTION
  WHEN duplicate_column THEN NULL;
END $$;

DO $$
BEGIN
  ALTER TABLE "auth_users" ADD COLUMN "email_verified_at" TIMESTAMP(3);
EXCEPTION
  WHEN duplicate_column THEN NULL;
END $$;

DO $$
BEGIN
  ALTER TABLE "auth_users" ADD COLUMN "totp_secret" TEXT;
EXCEPTION
  WHEN duplicate_column THEN NULL;
END $$;

DO $$
BEGIN
  ALTER TABLE "auth_users" ADD COLUMN "totp_enabled" BOOLEAN NOT NULL DEFAULT false;
EXCEPTION
  WHEN duplicate_column THEN NULL;
END $$;

-- Legacy rows: treat as already verified (same policy as new signups for now)
UPDATE "auth_users" SET "email_verified_at" = "createdAt" WHERE "email_verified_at" IS NULL;

-- CreateTable (Prisma default column names: camelCase)
CREATE TABLE IF NOT EXISTS "oauth_accounts" (
    "id" TEXT NOT NULL,
    "auth_user_id" TEXT NOT NULL,
    "provider" TEXT NOT NULL,
    "provider_user_id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "oauth_accounts_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "oauth_accounts_provider_provider_user_id_key" ON "oauth_accounts"("provider", "provider_user_id");

CREATE INDEX IF NOT EXISTS "oauth_accounts_auth_user_id_idx" ON "oauth_accounts"("auth_user_id");

DO $$
BEGIN
  ALTER TABLE "oauth_accounts" ADD CONSTRAINT "oauth_accounts_auth_user_id_fkey" FOREIGN KEY ("auth_user_id") REFERENCES "auth_users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;
