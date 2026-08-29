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
    CONSTRAINT uk_network_action_network_application UNIQUE (network_id, application_action_id)
);

CREATE INDEX IF NOT EXISTS idx_network_action_network ON network_action(network_id);
