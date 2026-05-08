create index if not exists idx_dark_tracking_reconcile
    on public.dark_tracking_record (ark_naan, state, oai_id)
    where ark is not null;
