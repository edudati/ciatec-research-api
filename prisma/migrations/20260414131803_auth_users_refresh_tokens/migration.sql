-- PostgreSQL: new enum values must be committed before they can be used in the same migration
-- transaction. Table changes that reference 'PLAYER' are in the following migration.
ALTER TYPE "UserRole" ADD VALUE 'PLAYER';
