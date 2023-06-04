-- Delete legacy tables
-- this migration fixes issue: lareferencia-shell#2 

BEGIN;

-- drop CONSTRAINT fk_prevalidator if exists
ALTER TABLE network DROP CONSTRAINT IF EXISTS fk_prevalidator;

-- create constraint named fk_prevalidator on network (pre_validator_id) referencing validator (id)
ALTER TABLE network ADD CONSTRAINT fk_prevalidator FOREIGN KEY (pre_validator_id) REFERENCES validator(id) ON DELETE NO ACTION;


-- drop CONSTRAINT fkbbkgd5g0hj337vag34y4obfni (validator_id) if exists
ALTER TABLE network DROP CONSTRAINT IF EXISTS fkbbkgd5g0hj337vag34y4obfni;
ALTER TABLE network DROP CONSTRAINT IF EXISTS fk_validator;

-- create constraint named fk_validator on network (validator_id) referencing validator (id) avoiding delete
ALTER TABLE network ADD CONSTRAINT fk_validator FOREIGN KEY (validator_id) REFERENCES validator(id) ON DELETE NO ACTION;


-- drop CONSTRAINT fkd2dwqqyr0lkyvmmo12vy2poru (secondary_transformer_id) if exists
ALTER TABLE network DROP CONSTRAINT IF EXISTS fkd2dwqqyr0lkyvmmo12vy2poru;
ALTER TABLE network DROP CONSTRAINT IF EXISTS fk_secondary_transformer;

-- create constraint named fk_secondary_transformer on network (secondary_transformer_id) referencing transformer (id) avoiding delete
ALTER TABLE network ADD CONSTRAINT fk_secondary_transformer FOREIGN KEY (secondary_transformer_id) REFERENCES transformer(id) ON DELETE NO ACTION;


-- drop CONSTRAINT fk_primary_transformer if exists
ALTER TABLE network DROP CONSTRAINT IF EXISTS fk_primary_transformer;

-- create constraint named fk_primary_transformer on network (transformer_id) referencing transformer (id) avoiding delete
ALTER TABLE network ADD CONSTRAINT fk_primary_transformer FOREIGN KEY (transformer_id) REFERENCES transformer(id) ON DELETE NO ACTION;


COMMIT;
