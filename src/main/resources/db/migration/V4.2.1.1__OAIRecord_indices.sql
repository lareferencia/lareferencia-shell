-- Create indices for optimizing queries on OAIRecord table

BEGIN;

CREATE INDEX oairecord_originalmetadatahash_idx ON public.oairecord USING btree (originalmetadatahash);
CREATE INDEX oairecord_publishedmetadatahash_idx ON public.oairecord USING btree (publishedmetadatahash);

COMMIT;
