ALTER TABLE oaiidentifierdark
  ADD COLUMN IF NOT EXISTS itemurl varchar(2048);

ALTER TABLE oaiidentifierdark
  ADD COLUMN IF NOT EXISTS lastmodified timestamp;

alter table darkcredential
drop constraint darkcredential_pkey;

alter table darkcredential
    add primary key (network_id);

A