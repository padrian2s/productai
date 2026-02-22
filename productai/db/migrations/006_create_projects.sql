-- Create projects table and link plans to projects.
-- Also expand versions + ai_sessions CHECK constraints to include 'project'.

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    status TEXT DEFAULT 'planning' CHECK(status IN ('planning', 'active', 'on_hold', 'completed', 'archived')),
    priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high', 'critical')),
    lead TEXT DEFAULT '',
    members TEXT DEFAULT '[]',
    milestones TEXT DEFAULT '[]',
    start_date TEXT DEFAULT '',
    target_date TEXT DEFAULT '',
    ai_conversation TEXT DEFAULT '[]',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Add project_id FK to plans
ALTER TABLE plans ADD COLUMN project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL;

-- Recreate versions table to add 'project' to CHECK constraint
CREATE TABLE IF NOT EXISTS versions_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('plan', 'prd', 'setting', 'project')),
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

-- Recreate ai_sessions table to add 'project' to CHECK constraint
CREATE TABLE IF NOT EXISTS ai_sessions_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('plan', 'prd', 'project')),
    entity_id INTEGER NOT NULL,
    messages TEXT DEFAULT '[]',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

INSERT INTO ai_sessions_new (id, entity_type, entity_id, messages, created_at, updated_at)
    SELECT id, entity_type, entity_id, messages, created_at, updated_at FROM ai_sessions;

DROP TABLE ai_sessions;

ALTER TABLE ai_sessions_new RENAME TO ai_sessions;
