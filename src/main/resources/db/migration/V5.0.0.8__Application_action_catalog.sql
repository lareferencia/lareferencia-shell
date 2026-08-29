CREATE TABLE IF NOT EXISTS application_action (
    id BIGSERIAL PRIMARY KEY,
    engine_type VARCHAR(32) NOT NULL,
    action_key VARCHAR(255) NOT NULL,
    enabled BOOLEAN NOT NULL,
    available BOOLEAN NOT NULL,
    definition JSONB NOT NULL DEFAULT '{}'::jsonb,
    configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_by VARCHAR(255),
    last_seen_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT uk_application_action_engine_key UNIQUE (engine_type, action_key)
);

CREATE INDEX IF NOT EXISTS idx_application_action_engine ON application_action (engine_type);
