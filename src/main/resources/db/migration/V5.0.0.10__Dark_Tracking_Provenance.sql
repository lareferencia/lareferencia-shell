ALTER TABLE public.dark_tracking_record
    ADD COLUMN IF NOT EXISTS source_network_id bigint,
    ADD COLUMN IF NOT EXISTS source_snapshot_id bigint;

CREATE INDEX IF NOT EXISTS idx_dark_tracking_source_network
    ON public.dark_tracking_record (source_network_id);
