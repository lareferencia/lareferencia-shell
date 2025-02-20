-- Create indices for optimizing queries on OAIRecord table

CREATE INDEX IF NOT EXISTS relation_from_entity_id_idx
ON public.relation (from_entity_id);

CREATE INDEX IF NOT EXISTS relation_to_entity_id_idx
ON public.relation (to_entity_id);

