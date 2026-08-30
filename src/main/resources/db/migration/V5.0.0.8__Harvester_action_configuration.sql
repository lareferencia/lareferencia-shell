-- Configurable action catalogue introduced by the harvester v5 API.
--
-- This migration intentionally keeps all new installation-level and
-- per-network action state together. The IF NOT EXISTS clauses also allow a
-- development database previously bootstrapped by Hibernate or by the earlier
-- split branch migrations to converge to the final schema.

CREATE TABLE IF NOT EXISTS application_action (
    id BIGSERIAL PRIMARY KEY,
    engine_type VARCHAR(32) NOT NULL,
    action_key VARCHAR(255) NOT NULL,
    enabled BOOLEAN NOT NULL,
    available BOOLEAN NOT NULL,
    execution_order INTEGER NOT NULL DEFAULT -1,
    definition JSONB NOT NULL DEFAULT '{}'::jsonb,
    configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_by VARCHAR(255),
    last_seen_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT uk_application_action_engine_key UNIQUE (engine_type, action_key)
);

-- Compatibility with databases that ran the earlier branch version of 5.0.0.8.
ALTER TABLE application_action
    ADD COLUMN IF NOT EXISTS execution_order INTEGER DEFAULT -1;
UPDATE application_action SET execution_order = -1 WHERE execution_order IS NULL;
ALTER TABLE application_action ALTER COLUMN execution_order SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_application_action_engine
    ON application_action (engine_type);
CREATE INDEX IF NOT EXISTS idx_application_action_engine_execution_order
    ON application_action (engine_type, execution_order);

CREATE TABLE IF NOT EXISTS network_action (
    id BIGSERIAL PRIMARY KEY,
    network_id BIGINT NOT NULL REFERENCES network(id) ON DELETE CASCADE,
    application_action_id BIGINT NOT NULL REFERENCES application_action(id) ON DELETE CASCADE,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    schedule_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_by VARCHAR(255),
    CONSTRAINT uk_network_action_network_application
        UNIQUE (network_id, application_action_id)
);

CREATE INDEX IF NOT EXISTS idx_network_action_network
    ON network_action (network_id);

CREATE TABLE IF NOT EXISTS application_worker_configuration (
    id BIGSERIAL PRIMARY KEY,
    engine_type VARCHAR(32) NOT NULL,
    worker_key VARCHAR(255) NOT NULL,
    available BOOLEAN NOT NULL,
    definition JSONB NOT NULL DEFAULT '{}'::jsonb,
    configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_by VARCHAR(255),
    last_seen_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT uk_application_worker_engine_key UNIQUE (engine_type, worker_key)
);

CREATE INDEX IF NOT EXISTS idx_application_worker_engine
    ON application_worker_configuration (engine_type);
