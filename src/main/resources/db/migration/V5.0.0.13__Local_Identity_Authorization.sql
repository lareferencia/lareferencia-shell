CREATE TABLE IF NOT EXISTS local_user (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    global_role VARCHAR(32) NOT NULL CHECK (global_role IN ('ADMIN', 'READER')),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS local_user_network_read (
    user_id BIGINT NOT NULL REFERENCES local_user(id) ON DELETE CASCADE,
    network_id BIGINT NOT NULL REFERENCES network(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, network_id)
);

CREATE TABLE IF NOT EXISTS local_service_account (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL UNIQUE,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS local_service_account_network_read (
    service_account_id BIGINT NOT NULL REFERENCES local_service_account(id) ON DELETE CASCADE,
    network_id BIGINT NOT NULL REFERENCES network(id) ON DELETE CASCADE,
    PRIMARY KEY (service_account_id, network_id)
);

CREATE TABLE IF NOT EXISTS local_api_token (
    id BIGSERIAL PRIMARY KEY,
    service_account_id BIGINT NOT NULL REFERENCES local_service_account(id) ON DELETE CASCADE,
    token_prefix VARCHAR(16) NOT NULL,
    token_hash CHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_local_api_token_account ON local_api_token(service_account_id);
CREATE INDEX IF NOT EXISTS ix_local_api_token_expiry ON local_api_token(expires_at) WHERE revoked_at IS NULL;

CREATE TABLE IF NOT EXISTS spring_session (
    primary_id CHAR(36) NOT NULL,
    session_id CHAR(36) NOT NULL,
    creation_time BIGINT NOT NULL,
    last_access_time BIGINT NOT NULL,
    max_inactive_interval INT NOT NULL,
    expiry_time BIGINT NOT NULL,
    principal_name VARCHAR(100),
    CONSTRAINT spring_session_pk PRIMARY KEY (primary_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS spring_session_ix1 ON spring_session(session_id);
CREATE INDEX IF NOT EXISTS spring_session_ix2 ON spring_session(expiry_time);
CREATE INDEX IF NOT EXISTS spring_session_ix3 ON spring_session(principal_name);

CREATE TABLE IF NOT EXISTS spring_session_attributes (
    session_primary_id CHAR(36) NOT NULL,
    attribute_name VARCHAR(200) NOT NULL,
    attribute_bytes BYTEA NOT NULL,
    CONSTRAINT spring_session_attributes_pk PRIMARY KEY (session_primary_id, attribute_name),
    CONSTRAINT spring_session_attributes_fk FOREIGN KEY (session_primary_id)
        REFERENCES spring_session(primary_id) ON DELETE CASCADE
);
