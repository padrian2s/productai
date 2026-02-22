"""Data access layer for projects, plans and PRDs."""

import json
from .schema import get_db, now_iso


# ── Projects ──────────────────────────────────────────

async def list_projects(status: str | None = None) -> list[dict]:
    db = await get_db()
    try:
        if status:
            cursor = await db.execute(
                "SELECT * FROM projects WHERE status = ? ORDER BY updated_at DESC", (status,)
            )
        else:
            cursor = await db.execute("SELECT * FROM projects ORDER BY updated_at DESC")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def get_project(project_id: int) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def create_project(title: str, description: str = "") -> int:
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO projects (title, description) VALUES (?, ?)",
            (title, description),
        )
        await db.commit()
        project_id = cursor.lastrowid
    finally:
        await db.close()
    await save_version("project", project_id, ["created"])
    return project_id


async def update_project(project_id: int, **fields) -> bool:
    if not fields:
        return False
    allowed = {
        "title", "description", "status", "priority", "lead",
        "members", "milestones", "start_date", "target_date",
        "ai_conversation",
    }
    filtered = {k: v for k, v in fields.items() if k in allowed}
    if not filtered:
        return False
    filtered["updated_at"] = now_iso()
    sets = ", ".join(f"{k} = ?" for k in filtered)
    vals = list(filtered.values()) + [project_id]
    db = await get_db()
    try:
        await db.execute(f"UPDATE projects SET {sets} WHERE id = ?", vals)
        await db.commit()
    finally:
        await db.close()
    changed = [k for k in filtered if k != "updated_at"]
    await save_version("project", project_id, changed)
    return True


async def delete_project(project_id: int) -> bool:
    await save_version("project", project_id, ["deleted"])
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


# ── Plans ──────────────────────────────────────────────

async def list_plans(status: str | None = None, project_id: int | None = None) -> list[dict]:
    db = await get_db()
    try:
        clauses, params = [], []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if project_id:
            clauses.append("project_id = ?")
            params.append(project_id)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        cursor = await db.execute(
            f"SELECT * FROM plans{where} ORDER BY updated_at DESC", params
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def get_plan(plan_id: int) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM plans WHERE id = ?", (plan_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def create_plan(title: str, description: str = "") -> int:
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO plans (title, description) VALUES (?, ?)",
            (title, description),
        )
        await db.commit()
        plan_id = cursor.lastrowid
    finally:
        await db.close()
    await save_version("plan", plan_id, ["created"])
    return plan_id


async def update_plan(plan_id: int, **fields) -> bool:
    if not fields:
        return False
    allowed = {
        "title", "description", "status", "vision", "goals",
        "target_audience", "success_metrics", "ai_conversation",
        "project_id",
    }
    filtered = {k: v for k, v in fields.items() if k in allowed}
    if not filtered:
        return False
    filtered["updated_at"] = now_iso()
    sets = ", ".join(f"{k} = ?" for k in filtered)
    vals = list(filtered.values()) + [plan_id]
    db = await get_db()
    try:
        await db.execute(f"UPDATE plans SET {sets} WHERE id = ?", vals)
        await db.commit()
    finally:
        await db.close()
    # Save version snapshot
    changed = [k for k in filtered if k != "updated_at"]
    await save_version("plan", plan_id, changed)
    return True


async def delete_plan(plan_id: int) -> bool:
    # Snapshot before deletion
    await save_version("plan", plan_id, ["deleted"])
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


# ── PRDs ───────────────────────────────────────────────

async def list_prds(plan_id: int | None = None) -> list[dict]:
    db = await get_db()
    try:
        if plan_id:
            cursor = await db.execute(
                "SELECT * FROM prds WHERE plan_id = ? ORDER BY updated_at DESC",
                (plan_id,),
            )
        else:
            cursor = await db.execute("SELECT * FROM prds ORDER BY updated_at DESC")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def get_prd(prd_id: int) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM prds WHERE id = ?", (prd_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def create_prd(title: str, plan_id: int | None = None) -> int:
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO prds (title, plan_id) VALUES (?, ?)",
            (title, plan_id),
        )
        await db.commit()
        prd_id = cursor.lastrowid
    finally:
        await db.close()
    await save_version("prd", prd_id, ["created"])
    return prd_id


async def update_prd(prd_id: int, **fields) -> bool:
    if not fields:
        return False
    allowed = {
        "title", "plan_id", "status", "content", "overview",
        "problem_statement", "proposed_solution", "user_stories",
        "requirements_functional", "requirements_nonfunctional",
        "success_metrics", "timeline", "ai_conversation",
    }
    filtered = {k: v for k, v in fields.items() if k in allowed}
    if not filtered:
        return False
    filtered["updated_at"] = now_iso()
    sets = ", ".join(f"{k} = ?" for k in filtered)
    vals = list(filtered.values()) + [prd_id]
    db = await get_db()
    try:
        await db.execute(f"UPDATE prds SET {sets} WHERE id = ?", vals)
        await db.commit()
    finally:
        await db.close()
    # Save version snapshot
    changed = [k for k in filtered if k != "updated_at"]
    await save_version("prd", prd_id, changed)
    return True


async def delete_prd(prd_id: int) -> bool:
    # Snapshot before deletion
    await save_version("prd", prd_id, ["deleted"])
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM prds WHERE id = ?", (prd_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


# ── AI Sessions ────────────────────────────────────────

async def get_or_create_session(entity_type: str, entity_id: int) -> dict:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM ai_sessions WHERE entity_type = ? AND entity_id = ?",
            (entity_type, entity_id),
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        cursor = await db.execute(
            "INSERT INTO ai_sessions (entity_type, entity_id) VALUES (?, ?)",
            (entity_type, entity_id),
        )
        await db.commit()
        return {
            "id": cursor.lastrowid,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "messages": "[]",
        }
    finally:
        await db.close()


async def append_session_message(
    entity_type: str, entity_id: int, role: str, content: str
):
    session = await get_or_create_session(entity_type, entity_id)
    messages = json.loads(session["messages"])
    messages.append({"role": role, "content": content})
    db = await get_db()
    try:
        await db.execute(
            "UPDATE ai_sessions SET messages = ?, updated_at = ? WHERE id = ?",
            (json.dumps(messages), now_iso(), session["id"]),
        )
        await db.commit()
    finally:
        await db.close()
    return messages


# ── Version History ────────────────────────────────────

async def save_version(entity_type: str, entity_id: int, changed_fields: list[str]):
    """Snapshot the current state of an entity as a new version."""
    if entity_type == "project":
        entity = await get_project(entity_id)
    elif entity_type == "plan":
        entity = await get_plan(entity_id)
    elif entity_type == "prd":
        entity = await get_prd(entity_id)
    else:
        return
    if not entity:
        return
    await _save_version_direct(entity_type, entity_id, entity, changed_fields)


async def _save_version_direct(
    entity_type: str, entity_id: int, snapshot_data: dict, changed_fields: list[str],
):
    """Insert a version row from a pre-built snapshot dict."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT COALESCE(MAX(version), 0) FROM versions WHERE entity_type = ? AND entity_id = ?",
            (entity_type, entity_id),
        )
        row = await cursor.fetchone()
        next_version = row[0] + 1

        await db.execute(
            "INSERT INTO versions (entity_type, entity_id, version, snapshot, changed_fields) VALUES (?, ?, ?, ?, ?)",
            (entity_type, entity_id, next_version, json.dumps(snapshot_data), ", ".join(changed_fields)),
        )
        await db.commit()
    finally:
        await db.close()


async def list_versions(entity_type: str, entity_id: int) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, version, changed_fields, created_at FROM versions "
            "WHERE entity_type = ? AND entity_id = ? ORDER BY version DESC",
            (entity_type, entity_id),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def get_version(version_id: int) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM versions WHERE id = ?", (version_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def get_current_version_number(entity_type: str, entity_id: int) -> int:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT COALESCE(MAX(version), 0) FROM versions WHERE entity_type = ? AND entity_id = ?",
            (entity_type, entity_id),
        )
        row = await cursor.fetchone()
        return row[0]
    finally:
        await db.close()


# ── Settings ───────────────────────────────────────────

async def get_setting(key: str) -> str | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row[0] if row else None
    finally:
        await db.close()


async def get_all_settings() -> dict:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT key, value, updated_at FROM settings ORDER BY key")
        rows = await cursor.fetchall()
        return {r["key"]: {"value": r["value"], "updated_at": r["updated_at"]} for r in rows}
    finally:
        await db.close()


async def update_setting(key: str, value: str) -> bool:
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = ?",
            (key, value, now_iso(), value, now_iso()),
        )
        await db.commit()
    finally:
        await db.close()
    # Track setting version
    entity_id = _setting_key_id(key)
    await _save_version_direct("setting", entity_id, {"key": key, "value": value}, [key])
    return True


# Stable numeric ID for a setting key (for version tracking)
_SETTING_KEY_IDS = {"enhance_light": 1, "enhance_medium": 2, "enhance_heavy": 3}


def _setting_key_id(key: str) -> int:
    return _SETTING_KEY_IDS.get(key, abs(hash(key)) % 1_000_000)
