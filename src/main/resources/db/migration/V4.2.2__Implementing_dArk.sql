create sequence public.oaiidentifierdark_id_seq;

create table public.oaiidentifierdark
(
    darkidentifier varchar(255) not null
        primary key,
    rawdarkidentifier varchar(255) not null,
    metadata       boolean      not null,
    oaiidentifier  varchar(255) not null,
    datestamp timestamp without time zone NOT NULL
);

create table public.darkcredential
(
    naan       bigint       not null
        primary key,
    privatekey varchar(255) not null
);
