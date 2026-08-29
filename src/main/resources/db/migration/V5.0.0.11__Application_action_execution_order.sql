ALTER TABLE application_action
    ADD COLUMN IF NOT EXISTS execution_order INTEGER;

-- -1 asks the first catalogue reconciliation to initialise the sequence from
-- the active executor's configured discovery order. This preserves legacy XML
-- order rather than fabricating an alphabetical order in SQL.
UPDATE application_action SET execution_order = -1;

ALTER TABLE application_action
    ALTER COLUMN execution_order SET NOT NULL;

CREATE INDEX idx_application_action_engine_execution_order
    ON application_action (engine_type, execution_order);
