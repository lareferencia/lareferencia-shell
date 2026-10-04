-- Keep the historical aggregate status; per-indexer results start empty.
-- Idempotent for installations that already applied the standalone SQL script.
-- Flyway manages the transaction for this migration.
ALTER TABLE networksnapshot ADD COLUMN IF NOT EXISTS indexing_results JSONB;

UPDATE networksnapshot
SET indexing_results = '{"generation":0,"results":{}}'::JSONB
WHERE indexing_results IS NULL;

ALTER TABLE networksnapshot ALTER COLUMN indexing_results
    SET DEFAULT '{"generation":0,"results":{}}'::JSONB;
ALTER TABLE networksnapshot ALTER COLUMN indexing_results SET NOT NULL;
