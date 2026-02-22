-- Seed v1 version snapshots for demo plan and PRD (if they don't already have versions).
-- This ensures the demo data created by 003 has trackable history.

INSERT OR IGNORE INTO versions (entity_type, entity_id, version, snapshot, changed_fields)
SELECT 'plan', id, 1, json_object(
    'id', id, 'title', title, 'description', description, 'status', status,
    'vision', vision, 'target_audience', target_audience,
    'created_at', created_at, 'updated_at', updated_at
), 'created'
FROM plans WHERE id = 1 AND NOT EXISTS (
    SELECT 1 FROM versions WHERE entity_type = 'plan' AND entity_id = 1
);

INSERT OR IGNORE INTO versions (entity_type, entity_id, version, snapshot, changed_fields)
SELECT 'prd', id, 1, json_object(
    'id', id, 'title', title, 'plan_id', plan_id, 'status', status,
    'content', content, 'overview', overview, 'problem_statement', problem_statement,
    'proposed_solution', proposed_solution, 'timeline', timeline,
    'created_at', created_at, 'updated_at', updated_at
), 'created'
FROM prds WHERE id = 1 AND NOT EXISTS (
    SELECT 1 FROM versions WHERE entity_type = 'prd' AND entity_id = 1
);
