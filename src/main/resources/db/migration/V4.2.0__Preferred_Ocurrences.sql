-- Delete legacy fields in network table

BEGIN;

ALTER TABLE public.field_occurrence ADD preferred bool NOT NULL DEFAULT false;

COMMIT;
