-- upgrade --
ALTER TABLE "ballinstance" ADD "shiny" BOOL NOT NULL  DEFAULT False;
ALTER TABLE "ballinstance" ADD "booster" BOOL NOT NULL DEFAULT False;
ALTER TABLE "ballinstance" DROP COLUMN "special";
-- downgrade --
ALTER TABLE "ballinstance" ADD "special" INT NOT NULL  DEFAULT 0;
ALTER TABLE "ballinstance" DROP COLUMN "shiny";
ALTER TABLE "ballinstance" DROP COLUMN "booster";
