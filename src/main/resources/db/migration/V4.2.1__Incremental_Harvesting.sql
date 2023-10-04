-- Delete legacy fields in network table

BEGIN;

ALTER TABLE public.networksnapshot ADD previoussnapshotid int8 NULL;

COMMIT;
