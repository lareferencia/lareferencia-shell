-- Delete legacy tables
-- this migration fixes issue: lareferencia-shell#2 

BEGIN;


-- DROP TABLE "networkproperty" --------------------------------
DROP TABLE IF EXISTS "networkproperty" CASCADE;
-- -------------------------------------------------------------

-- DROP TABLE "oaiset" -----------------------------------------
DROP TABLE IF EXISTS "oaiset" CASCADE;
-- -------------------------------------------------------------

-- DROP TABLE "oaiorigin" --------------------------------------
DROP TABLE IF EXISTS "oaiorigin" CASCADE;
-- -------------------------------------------------------------

COMMIT;
