-- No initial row: installations retain property defaults until the first Admin save.
CREATE TABLE taskmanager_configuration (
    id BIGINT PRIMARY KEY CHECK (id = 1),
    concurrent_tasks INTEGER NOT NULL CHECK (concurrent_tasks >= 1),
    max_queued_tasks INTEGER NOT NULL CHECK (max_queued_tasks >= 0),
    result_retention_seconds BIGINT NOT NULL CHECK (result_retention_seconds >= 1),
    max_retained_results INTEGER NOT NULL CHECK (max_retained_results >= 1),
    shutdown_timeout_seconds BIGINT NOT NULL CHECK (shutdown_timeout_seconds >= 0),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_by VARCHAR(255)
);
