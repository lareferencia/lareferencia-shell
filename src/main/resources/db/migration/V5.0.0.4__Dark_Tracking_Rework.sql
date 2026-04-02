drop table if exists public.dark_tracking_record;

-- drop table if exists public.oaiidentifierdark;
-- drop table if exists public.darkcredential;
-- drop sequence if exists public.oaiidentifierdark_id_seq;

create table public.dark_tracking_record
(
    ark_naan             varchar(64)   not null,
    oai_id               varchar(512)  not null,
    ark                  varchar(255),
    source_metadata_hash varchar(128),
    target_url           varchar(2000),
    state                varchar(1)    not null
        constraint dark_tracking_record_state_chk
            check (state in ('R', 'D', 'U', 'P', 'T', 'E')),
    last_error           varchar(4000),
    created_at           timestamp     not null,
    updated_at           timestamp     not null,
    last_staged_at       timestamp,
    last_reconciled_at   timestamp,
    published_at         timestamp,
    constraint dark_tracking_record_pkey
        primary key (ark_naan, oai_id)
);

create unique index uk_dark_tracking_record_ark
    on public.dark_tracking_record (ark);

create index idx_dark_tracking_state
    on public.dark_tracking_record (state);
