-- dARK minter v1 accepts the canonical ARK spelling: ark:NAAN/name.
-- Keep legacy rows usable while ensuring every persisted tracking value is canonical.
UPDATE public.dark_tracking_record
SET ark = 'ark:' || substring(ark FROM 6)
WHERE ark LIKE 'ark:/%';
