-- Expand versions table to also track 'setting' entity type.
-- SQLite does not support ALTER CHECK, so we recreate the table.

CREATE TABLE IF NOT EXISTS versions_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('plan', 'prd', 'setting')),
    entity_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    snapshot TEXT NOT NULL,
    changed_fields TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now'))
);

INSERT INTO versions_new (id, entity_type, entity_id, version, snapshot, changed_fields, created_at)
    SELECT id, entity_type, entity_id, version, snapshot, changed_fields, created_at FROM versions;

DROP TABLE versions;

ALTER TABLE versions_new RENAME TO versions;
