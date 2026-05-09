-- PostgreSQL: new enum values must be committed before they can be used in the
-- same transaction. Adding PI and PARTICIPANT to UserRole.
ALTER TYPE "UserRole" ADD VALUE 'PI';
ALTER TYPE "UserRole" ADD VALUE 'PARTICIPANT';
