ALTER TABLE entity
ADD COLUMN IF NOT EXISTS deleted boolean NOT NULL DEFAULT FALSE;

UPDATE entity
SET deleted = FALSE
WHERE deleted IS NULL;

CREATE INDEX IF NOT EXISTS idx_entity_dirty_deleted
ON entity (dirty, deleted);

CREATE INDEX IF NOT EXISTS idx_entity_type_dirty_deleted
ON entity (entity_type_id, dirty, deleted);
