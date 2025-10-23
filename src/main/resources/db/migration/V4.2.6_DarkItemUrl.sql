alter table oaiidentifierdark
    add itemurl varchar(2048);

alter table oaiidentifierdark
    add lastmodified timestamp;

alter table darkcredential
drop constraint darkcredential_pkey;

alter table darkcredential
    add primary key (network_id);
