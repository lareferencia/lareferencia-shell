ALTER TABLE field_type
ADD COLUMN IF NOT EXISTS subfields TEXT NULL DEFAULT '[]';

UPDATE field_type 
SET subfields = j.subfields_json
FROM 
(SELECT parent.id, concat('[',string_agg(format('"%s"', child.name), ', '),']') AS subfields_json 
FROM field_type parent, field_type child
WHERE parent.kind = 1 
AND parent.parent_field_type_id IS NULL 
AND child.parent_field_type_id = parent.id 
GROUP BY parent.id ) AS j 
WHERE field_type.id = j.id;

-- solve sematic_id length issues
ALTER TABLE semantic_identifier
ALTER COLUMN semantic_id TYPE TEXT;

DROP PROCEDURE IF EXISTS merge_entity_relation_data(integer);

CREATE PROCEDURE merge_entity_relation_data(INOUT ret integer)
    LANGUAGE sql
    AS $$	


	-- Delete occrs from dirty entities
	DELETE FROM entity_fieldoccr efo
	USING entity e
	WHERE efo.entity_id = e.uuid AND e.dirty = true;
	
	-- Insert occrs from related (non deleted) source entities into entities
	INSERT INTO entity_fieldoccr
	SELECT DISTINCT e.uuid, sef.fieldoccr_id
	FROM source_entity_fieldoccr sef, source_entity se, entity e
	WHERE e.dirty = TRUE AND se.deleted = FALSE AND sef.entity_id = se.uuid AND e.uuid = se.final_entity_id;
	
	-- Update relations using source entities relations as a base, avoiding duplicate relations
	INSERT INTO relation (relation_type_id, from_entity_id, to_entity_id, dirty)
	SELECT DISTINCT sr.relation_type_id, e1.uuid AS from_entity_id, e2.uuid AS to_entity_id, TRUE 
	FROM source_relation sr, source_entity se1, source_entity se2, entity e1, entity e2
	WHERE (e1.dirty = TRUE OR e2.dirty = TRUE) AND se1.deleted = FALSE AND se2.deleted = FALSE 
	AND sr.from_entity_id = se1.uuid AND sr.to_entity_id = se2.uuid 
	AND se1.final_entity_id = e1.uuid AND se2.final_entity_id = e2.uuid 
	AND NOT EXISTS (SELECT * FROM relation x WHERE x.relation_type_id = sr.relation_type_id AND x.from_entity_id = e1.uuid AND x.to_entity_id = e2.uuid );
	
	-- Delete dirty relations field occrs 
	DELETE FROM relation_fieldoccr rfo
	USING relation r
	WHERE r.dirty = TRUE AND r.relation_type_id = rfo.relation_type_id AND r.from_entity_id = rfo.from_entity_id AND r.to_entity_id = rfo.to_entity_id;
	
	-- Insert field occrs from dirty relations using source relations as base
	INSERT INTO relation_fieldoccr (from_entity_id, relation_type_id, to_entity_id, fieldoccr_id)
	SELECT DISTINCT r.from_entity_id, r.relation_type_id, r.to_entity_id,  sro.fieldoccr_id
	FROM relation r, source_entity se1, source_entity se2, source_relation_fieldoccr sro
	WHERE r.dirty = TRUE AND r.from_entity_id = se1.final_entity_id AND r.to_entity_id = se2.final_entity_id AND sro.from_entity_id = se1.uuid AND sro.to_entity_id = se2.uuid AND sro.relation_type_id = r.relation_type_id;
	
	-- set entities and relations as non-dirty
	UPDATE entity 
	SET dirty = FALSE
	WHERE dirty = TRUE;
	
	UPDATE relation 
	SET dirty = FALSE
	WHERE dirty = TRUE;
	
	SELECT 1;
	
$$;

