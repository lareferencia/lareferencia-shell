ALTER TABLE oaiidentifierdark
  ADD COLUMN IF NOT EXISTS itemurl varchar(2048);

ALTER TABLE oaiidentifierdark
  ADD COLUMN IF NOT EXISTS lastmodified timestamp;

ALTER TABLE darkcredential
  DROP CONSTRAINT IF EXISTS darkcredential_pkey;

ALTER TABLE darkcredential
  ADD CONSTRAINT IF NOT EXISTS darkcredential_pkey
  PRIMARY KEY (network_id);