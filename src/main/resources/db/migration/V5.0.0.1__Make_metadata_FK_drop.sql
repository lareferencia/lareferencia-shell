-- Migration to remove metadata foreign key constraints for Spring Boot 3.x / Hibernate 6.x compatibility
-- The foreign keys caused issues with entity persistence order in Hibernate 6.x
-- Application logic ensures referential integrity without database-level constraints

-- Drop existing foreign key constraints if they exist
ALTER TABLE oairecord DROP CONSTRAINT IF EXISTS oairecord_fk;
ALTER TABLE oairecord DROP CONSTRAINT IF EXISTS oairecord_published_fk;

-- Keep indices for query performance even without foreign keys
CREATE INDEX IF NOT EXISTS idx_oairecord_original_metadata 
ON oairecord(originalmetadatahash);

CREATE INDEX IF NOT EXISTS idx_oairecord_published_metadata 
ON oairecord(publishedmetadatahash);
