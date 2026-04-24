-- Replaces level UUIDs with RFC 4122--valid variants so Zod .uuid() accepts them (4th group must be 8/9/a/b, not 0..7).
-- FKs use ON UPDATE CASCADE, so child tables follow.

UPDATE "levels" SET "id" = '0a23e6c8-3d4f-4a5b-8b1a-2e3f4a5b6c7d' WHERE "id" = '0a23e6c8-3d4f-4a5b-0b1a-2e3f4a5b6c7d';
UPDATE "levels" SET "id" = '1b34f7d9-4e5a-4b6c-8d1e-2f3a4b5c6d7e' WHERE "id" = '1b34f7d9-4e5a-4b6c-0d1e-2f3a4b5c6d7e';
