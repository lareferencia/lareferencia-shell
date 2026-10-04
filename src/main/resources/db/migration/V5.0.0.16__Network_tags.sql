CREATE TABLE network_tag (
    network_id BIGINT NOT NULL REFERENCES network(id) ON DELETE CASCADE,
    tag VARCHAR(100) NOT NULL,
    PRIMARY KEY (network_id, tag)
);
CREATE INDEX network_tag_tag_network_idx ON network_tag(tag, network_id);
