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

CREATE INDEX IF NOT EXISTS idx_application_worker_engine ON application_worker_configuration (engine_type);
