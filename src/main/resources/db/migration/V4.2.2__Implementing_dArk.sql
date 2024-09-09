drop sequence if exists public.oaiidentifierdark_id_seq;
create sequence public.oaiidentifierdark_id_seq start 1 increment 1;


drop table if exists public.oaiidentifierdark;
create table public.oaiidentifierdark
(
    darkidentifier    varchar(255) not null
        primary key,
    rawdarkidentifier varchar(255) not null,
    oaiidentifier     varchar(255) not null,
    datestamp         timestamp    not null
);

DROP TABLE IF EXISTS public.darkcredential;
create table public.darkcredential
(
    naan       bigint       not null
        primary key,
    privatekey varchar(255) not null,
    network_id bigint      not null
        constraint darkcredential_network_fk
            references public.network
);


