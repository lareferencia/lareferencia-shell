-- =====================================================
-- Migration: V5.0.1
-- Description: Create merge_dirty_entities_and_relations function for merging dirty entities and relations
-- Purpose: Consolidates dirty entities and relations from source_entity/source_relation to entity/relation tables
-- =====================================================

-- Drop existing functions if they exist
DROP FUNCTION IF EXISTS merge_dirty_entities_and_relations();
DROP FUNCTION IF EXISTS process_dirty_entities();

-- Drop old merge procedure if it exists (legacy compatibility)
DROP PROCEDURE IF EXISTS merge_entity_relation_data(INTEGER);

-- Create the merge_dirty_entities_and_relations function
-- This function merges dirty entities and their relations from source tables to final tables
CREATE OR REPLACE FUNCTION merge_dirty_entities_and_relations()
RETURNS VOID AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    duration INTERVAL;
BEGIN
    -- Log process start
    start_time := clock_timestamp();
    RAISE NOTICE 'Starting dirty entities merge process (with triggers disabled): %', start_time;

    -- Preparation for merge
    RAISE NOTICE 'Starting merge preparation process: %', start_time;

    -- Create unified auxiliary table with dirty entities and their source entities
    RAISE NOTICE 'Creating unified auxiliary table for dirty entities and their source entities...';

    -- Drop auxiliary table if it already exists
    DROP TABLE IF EXISTS aux_entity_map;
    CREATE TABLE aux_entity_map (
        entity_id UUID NOT NULL,
        source_id UUID
    );

    -- Insert dirty entities with their source_entities
    INSERT INTO aux_entity_map (entity_id, source_id)
    SELECT e.uuid, se.uuid
    FROM entity e
    JOIN source_entity se ON se.final_entity_id = e.uuid
    WHERE e.dirty = TRUE;

    -- Create indexes on auxiliary table
    CREATE INDEX ON aux_entity_map(entity_id);
    CREATE INDEX ON aux_entity_map(source_id);

    -- Create temporary table for fieldoccrs to insert
    RAISE NOTICE 'Creating temporary table for fieldoccrs...';
    DROP TABLE IF EXISTS tmp_entity_fieldoccrs;
    CREATE TEMP TABLE tmp_entity_fieldoccrs AS
    SELECT DISTINCT aem.entity_id, sef.fieldoccr_id
    FROM aux_entity_map aem
    JOIN source_entity_fieldoccr sef ON sef.entity_id = aem.source_id
    WHERE aem.source_id IS NOT NULL;
    CREATE INDEX ON tmp_entity_fieldoccrs(entity_id);

    -- Efficiently delete existing fieldoccrs
    RAISE NOTICE 'Deleting existing fieldoccrs...';
    DELETE FROM entity_fieldoccr
    WHERE entity_id IN (SELECT DISTINCT entity_id FROM aux_entity_map);

    -- Insert new fieldoccrs
    RAISE NOTICE 'Inserting new fieldoccrs...';
    INSERT INTO entity_fieldoccr (entity_id, fieldoccr_id)
    SELECT entity_id, fieldoccr_id FROM tmp_entity_fieldoccrs;

    -- Update dirty state of entities
    RAISE NOTICE 'Updating dirty state of entities...';
    UPDATE entity
    SET dirty = FALSE
    WHERE uuid IN (SELECT DISTINCT entity_id FROM aux_entity_map);

    -- Relations merge process
    RAISE NOTICE 'Starting relations merge process (with triggers disabled): %', start_time;

    -- Create temporary table for new relations
    RAISE NOTICE 'Creating temporary table for new relations...';
    DROP TABLE IF EXISTS tmp_new_relations;
    CREATE TABLE tmp_new_relations (
        from_entity_id UUID,
        relation_type_id int8,
        to_entity_id UUID,
        source_from_entity_id UUID,
        source_to_entity_id UUID,
        dirty BOOLEAN
    );

    -- Add uniqueness constraint
    ALTER TABLE tmp_new_relations ADD CONSTRAINT unique_tmp_new_relations UNIQUE (from_entity_id, relation_type_id, to_entity_id);

    -- Insert new relations into temporary table
    INSERT INTO tmp_new_relations (from_entity_id, relation_type_id, to_entity_id, source_from_entity_id, source_to_entity_id, dirty)
    SELECT 
        se1.final_entity_id as from_entity_id,
        sr.relation_type_id,
        se2.final_entity_id as to_entity_id,
        sr.from_entity_id as source_from_entity_id,
        sr.to_entity_id as source_to_entity_id,
        true as dirty
    FROM source_relation sr
    JOIN source_entity se1 ON sr.from_entity_id = se1.uuid
    JOIN source_entity se2 ON sr.to_entity_id = se2.uuid
    WHERE (EXISTS (SELECT 1 FROM aux_entity_map aem WHERE aem.source_id = sr.from_entity_id)
        OR EXISTS (SELECT 1 FROM aux_entity_map aem WHERE aem.source_id = sr.to_entity_id))
    AND se1.deleted = FALSE -- Ensure source entities are not deleted
    AND se2.deleted = FALSE
    AND se1.final_entity_id IS NOT NULL -- Ensure they have final mapping
    AND se2.final_entity_id IS NOT NULL
    ON CONFLICT (from_entity_id, relation_type_id, to_entity_id) DO NOTHING;

    -- Create indexes to optimize subsequent queries
    CREATE INDEX ON tmp_new_relations(relation_type_id, from_entity_id, to_entity_id);
    CREATE INDEX ON tmp_new_relations(source_from_entity_id);
    CREATE INDEX ON tmp_new_relations(source_to_entity_id);

    -- Delete old relations involving dirty entities
    RAISE NOTICE 'Deleting old relations from dirty entities...';
    DELETE FROM relation r
    WHERE EXISTS (
        SELECT 1 FROM aux_entity_map aem
        WHERE aem.entity_id = r.from_entity_id OR aem.entity_id = r.to_entity_id
    );

    -- Create unique index for relations if it doesn't exist
    CREATE UNIQUE INDEX IF NOT EXISTS idx_rel_unique ON relation (relation_type_id, from_entity_id, to_entity_id);

    -- Insert new relations
    RAISE NOTICE 'Inserting new relations...';
    INSERT INTO relation (relation_type_id, from_entity_id, to_entity_id, dirty)
    SELECT tnr.relation_type_id,
        tnr.from_entity_id,
        tnr.to_entity_id,
        true
    FROM tmp_new_relations tnr
    ON CONFLICT (relation_type_id, from_entity_id, to_entity_id) DO NOTHING;

    -- Delete relation_fieldoccr for relations marked as dirty
    RAISE NOTICE 'Deleting relation_fieldoccr for dirty relations...';
    DELETE FROM relation_fieldoccr rfo
    WHERE EXISTS (
        SELECT 1 FROM relation r
        WHERE r.dirty = TRUE
          AND rfo.relation_type_id = r.relation_type_id
          AND rfo.from_entity_id = r.from_entity_id
          AND rfo.to_entity_id = r.to_entity_id
    );

    -- Insert relation fields for dirty relations
    RAISE NOTICE 'Inserting relation fields for dirty relations...';
    INSERT INTO relation_fieldoccr (from_entity_id, relation_type_id, to_entity_id, fieldoccr_id)
    SELECT
        tnr.from_entity_id,
        tnr.relation_type_id,
        tnr.to_entity_id,
        sro.fieldoccr_id
    FROM tmp_new_relations tnr
    JOIN source_relation_fieldoccr sro ON sro.relation_type_id = tnr.relation_type_id
                                    AND sro.from_entity_id = tnr.source_from_entity_id
                                    AND sro.to_entity_id = tnr.source_to_entity_id
    ON CONFLICT (from_entity_id, relation_type_id, to_entity_id, fieldoccr_id) DO NOTHING;

    RAISE NOTICE 'Relation fields insertion completed';

    -- Update dirty state of relations
    RAISE NOTICE 'Updating dirty state of relations...';
    UPDATE relation
    SET dirty = FALSE
    WHERE dirty = TRUE;

    -- Calculate process duration
    end_time := clock_timestamp();
    duration := end_time - start_time;

    -- Finalize process
    RAISE NOTICE 'Entity merge process completed successfully';
    RAISE NOTICE 'Entity merge duration: % seconds', EXTRACT(EPOCH FROM duration);
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- End of migration
-- =====================================================
