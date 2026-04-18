ALTER TABLE "User" ADD COLUMN IF NOT EXISTS "role" varchar NOT NULL DEFAULT 'user';
ALTER TABLE "User" ADD COLUMN IF NOT EXISTS "fullName" text NOT NULL DEFAULT '';
UPDATE "User" SET "role" = 'user' WHERE "role" <> 'user';

CREATE TABLE IF NOT EXISTS "PublicProfile" (
  "userId" uuid PRIMARY KEY NOT NULL REFERENCES "User"("id"),
  "fullName" text NOT NULL DEFAULT '',
  "updatedAt" timestamp NOT NULL DEFAULT now()
);
