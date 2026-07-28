alter table public.dark_tracking_record
    add column if not exists stage_payload_hash varchar(64);
