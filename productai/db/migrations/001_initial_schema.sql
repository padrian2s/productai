-- Initial schema: plans, prds, ai_sessions, settings, versions

CREATE TABLE IF NOT EXISTS plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'active', 'completed', 'archived')),
    vision TEXT DEFAULT '',
    goals TEXT DEFAULT '[]',
    target_audience TEXT DEFAULT '',
    success_metrics TEXT DEFAULT '[]',
    ai_conversation TEXT DEFAULT '[]',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS prds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'review', 'approved', 'archived')),
    content TEXT DEFAULT '',
    overview TEXT DEFAULT '',
    problem_statement TEXT DEFAULT '',
    proposed_solution TEXT DEFAULT '',
    user_stories TEXT DEFAULT '[]',
    requirements_functional TEXT DEFAULT '[]',
    requirements_nonfunctional TEXT DEFAULT '[]',
    success_metrics TEXT DEFAULT '[]',
    timeline TEXT DEFAULT '',
    ai_conversation TEXT DEFAULT '[]',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS ai_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('plan', 'prd')),
    entity_id INTEGER NOT NULL,
    messages TEXT DEFAULT '[]',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('plan', 'prd')),
    entity_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    snapshot TEXT NOT NULL,
    changed_fields TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now'))
);
