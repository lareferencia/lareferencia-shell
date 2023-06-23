-- Delete legacy fields in network table

BEGIN;

ALTER TABLE public.network DROP COLUMN attributesjsonserialization;

COMMIT;
