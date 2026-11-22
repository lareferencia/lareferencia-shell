CREATE TABLE IF NOT EXISTS package (
    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
    version INTEGER NOT NULL, network TEXT NOT NULL, snapshot TEXT NOT NULL, variant TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY, producer TEXT NOT NULL, run_key TEXT NOT NULL, metadata TEXT NOT NULL,
    UNIQUE(producer, run_key)
);
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY, catalog_id TEXT NOT NULL UNIQUE, identifier TEXT NOT NULL, metadata_hash TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS items_identifier ON items(identifier);
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY, item INTEGER NOT NULL REFERENCES items, producer TEXT NOT NULL,
    run INTEGER NOT NULL REFERENCES runs, generated_at TEXT NOT NULL, source_ref TEXT,
    UNIQUE(item, producer)
);
CREATE TABLE IF NOT EXISTS occurrences (
    id INTEGER PRIMARY KEY, target TEXT NOT NULL, content TEXT NOT NULL, UNIQUE(target, content)
);
CREATE TABLE IF NOT EXISTS result_occurrences (
    result INTEGER NOT NULL REFERENCES results, position INTEGER NOT NULL, occurrence INTEGER NOT NULL REFERENCES occurrences,
    PRIMARY KEY(result, position)
) WITHOUT ROWID;
