"""API routes — data operations and AI streaming."""

import json
import os
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from ..db import models
from ..ai import service as ai_service
from ..ai import autocomplete as ac

BASE_PATH = os.environ.get("BASE_PATH", "").rstrip("/")

router = APIRouter(prefix="/api")


# ── Projects CRUD ──────────────────────────────────────

@router.post("/projects")
async def create_project(request: Request):
    form = await request.form()
    title = form.get("title", "").strip()
    description = form.get("description", "").strip()
    if not title:
        return RedirectResponse(f"{BASE_PATH}/", status_code=303)
    project_id = await models.create_project(title, description)
    # Apply optional fields from create form
    fields = {}
    for key in ("status", "priority", "lead", "start_date", "target_date", "members", "milestones"):
        val = form.get(key, "").strip()
        if val:
            fields[key] = val
    if fields:
        await models.update_project(project_id, **fields)
    return RedirectResponse(f"{BASE_PATH}/projects/{project_id}", status_code=303)


@router.post("/projects/{project_id}")
async def update_project(project_id: int, request: Request):
    form = await request.form()
    fields = {k: v for k, v in form.items() if v}
    await models.update_project(project_id, **fields)
    return RedirectResponse(f"{BASE_PATH}/projects/{project_id}", status_code=303)


@router.post("/projects/{project_id}/delete")
async def delete_project(project_id: int):
    await models.delete_project(project_id)
    return RedirectResponse(f"{BASE_PATH}/", status_code=303)


# ── Plans CRUD ─────────────────────────────────────────

@router.post("/plans")
async def create_plan(title: str = Form(...), description: str = Form("")):
    plan_id = await models.create_plan(title, description)
    return RedirectResponse(f"{BASE_PATH}/plans/{plan_id}", status_code=303)


@router.post("/plans/{plan_id}")
async def update_plan(plan_id: int, request: Request):
    form = await request.form()
    fields = {k: v for k, v in form.items() if v}
    await models.update_plan(plan_id, **fields)
    return RedirectResponse(f"{BASE_PATH}/plans/{plan_id}", status_code=303)


@router.post("/plans/{plan_id}/delete")
async def delete_plan(plan_id: int):
    await models.delete_plan(plan_id)
    return RedirectResponse(f"{BASE_PATH}/", status_code=303)


# ── PRDs CRUD ──────────────────────────────────────────

@router.post("/prds")
async def create_prd(
    title: str = Form(...),
    plan_id: str = Form(""),
):
    pid = int(plan_id) if plan_id else None
    prd_id = await models.create_prd(title, pid)
    return RedirectResponse(f"{BASE_PATH}/prds/{prd_id}/edit", status_code=303)


@router.post("/prds/{prd_id}")
async def update_prd(prd_id: int, request: Request):
    form = await request.form()
    fields = {k: v for k, v in form.items() if v}
    await models.update_prd(prd_id, **fields)
    referer = request.headers.get("referer", f"{BASE_PATH}/prds/{prd_id}")
    return RedirectResponse(referer, status_code=303)


@router.post("/prds/{prd_id}/delete")
async def delete_prd(prd_id: int):
    await models.delete_prd(prd_id)
    return RedirectResponse(f"{BASE_PATH}/", status_code=303)


# ── Admin Settings ─────────────────────────────────────

@router.post("/admin/settings")
async def update_settings(request: Request):
    form = await request.form()
    for key in ("enhance_light", "enhance_medium", "enhance_heavy"):
        value = form.get(key, "").strip()
        if value:
            await models.update_setting(key, value)
    # API key (only stored when no env var is set)
    api_key = form.get("anthropic_api_key", "").strip()
    if api_key:
        await models.update_setting("anthropic_api_key", api_key)
        ai_service.invalidate_api_key_cache()
    return RedirectResponse(f"{BASE_PATH}/admin", status_code=303)


# ── Autocomplete ───────────────────────────────────────

@router.post("/autocomplete/words")
async def autocomplete_words(request: Request):
    """Return word suggestions for autocomplete."""
    body = await request.json()
    prefix = body.get("prefix", "")
    context = body.get("context")
    limit = min(body.get("limit", 8), 15)
    suggestions = ac.get_suggestions(prefix, context, limit)
    return {"suggestions": suggestions, "prefix": prefix}


# ── AI Streaming Endpoints ─────────────────────────────

@router.post("/ai/enhance")
async def enhance_field_stream(request: Request):
    """Stream AI-enhanced version of a text field."""
    form = await request.form()
    text = form.get("text", "").strip()
    field_label = form.get("field_label", "text")
    intensity = form.get("intensity", "medium")
    instruction = form.get("instruction", "").strip()

    if not text:
        return HTMLResponse("")

    if intensity not in ("light", "medium", "heavy"):
        intensity = "medium"

    async def event_stream():
        full_response = []
        async for token in ai_service.stream_enhance_field(text, field_label, intensity, instruction):
            full_response.append(token)
            yield f"data: {json.dumps({'token': token})}\n\n"
        complete = "".join(full_response)
        yield f"data: {json.dumps({'done': True, 'content': complete})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/ai/enhance-selection")
async def enhance_selection_stream(request: Request):
    """Stream AI-enhanced version of a selected portion of text."""
    form = await request.form()
    full_text = form.get("full_text", "").strip()
    selected_text = form.get("selected_text", "").strip()
    field_label = form.get("field_label", "text")
    intensity = form.get("intensity", "medium")
    instruction = form.get("instruction", "").strip()

    if not selected_text:
        return HTMLResponse("")

    if intensity not in ("light", "medium", "heavy"):
        intensity = "medium"

    async def event_stream():
        full_response = []
        async for token in ai_service.stream_enhance_selection(
            full_text, selected_text, field_label, intensity, instruction
        ):
            full_response.append(token)
            yield f"data: {json.dumps({'token': token})}\n\n"
        complete = "".join(full_response)
        yield f"data: {json.dumps({'done': True, 'content': complete})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/ai/plan/{plan_id}/chat")
async def plan_chat_stream(plan_id: int, request: Request):
    """Stream AI response for plan-mode conversation."""
    form = await request.form()
    user_message = form.get("message", "")
    if not user_message:
        return HTMLResponse("")

    # Save user message
    messages = await models.append_session_message("plan", plan_id, "user", user_message)

    # Build Claude messages format
    claude_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in messages
    ]

    async def event_stream():
        full_response = []
        async for token in ai_service.stream_plan_chat(claude_messages):
            full_response.append(token)
            escaped = token.replace("\n", "\\n").replace('"', '\\"')
            yield f"data: {json.dumps({'token': token})}\n\n"

        # Save assistant response
        complete = "".join(full_response)
        await models.append_session_message("plan", plan_id, "assistant", complete)
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/ai/prd/generate")
async def prd_generate_stream(request: Request):
    """Stream AI-generated PRD from context description."""
    form = await request.form()
    context = form.get("context", "")
    prd_id = form.get("prd_id", "")

    if not context:
        return HTMLResponse("")

    async def event_stream():
        full_response = []
        async for token in ai_service.stream_prd_generation(context):
            full_response.append(token)
            yield f"data: {json.dumps({'token': token})}\n\n"

        complete = "".join(full_response)
        if prd_id:
            await models.update_prd(int(prd_id), content=complete)
        yield f"data: {json.dumps({'done': True, 'content': complete})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/ai/prd/{prd_id}/chat")
async def prd_chat_stream(prd_id: int, request: Request):
    """Stream AI response for PRD refinement conversation."""
    form = await request.form()
    user_message = form.get("message", "")
    if not user_message:
        return HTMLResponse("")

    prd = await models.get_prd(prd_id)
    messages = await models.append_session_message("prd", prd_id, "user", user_message)

    claude_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in messages
    ]

    async def event_stream():
        full_response = []
        async for token in ai_service.stream_prd_refinement(
            prd["content"] or "", user_message, claude_messages[:-1]
        ):
            full_response.append(token)
            yield f"data: {json.dumps({'token': token})}\n\n"

        complete = "".join(full_response)
        await models.append_session_message("prd", prd_id, "assistant", complete)
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── Mindmap Data ──────────────────────────────────────

@router.get("/mindmap/data")
async def mindmap_data():
    """Return project hierarchy as a mindmap tree structure."""
    projects = await models.list_projects()
    all_plans = await models.list_plans()
    all_prds = await models.list_prds()

    # Index PRDs by plan_id
    prds_by_plan: dict[int | None, list[dict]] = {}
    for prd in all_prds:
        prds_by_plan.setdefault(prd.get("plan_id"), []).append(prd)

    # Index plans by project_id
    plans_by_project: dict[int | None, list[dict]] = {}
    for plan in all_plans:
        plan["prds"] = prds_by_plan.get(plan["id"], [])
        plans_by_project.setdefault(plan.get("project_id"), []).append(plan)

    def prd_node(prd):
        return {
            "name": prd["title"],
            "description": prd.get("overview") or prd.get("problem_statement") or "",
            "_type": "prd",
            "_url": f"{BASE_PATH}/prds/{prd['id']}",
            "_status": prd.get("status", "draft"),
        }

    def plan_node(plan):
        children = [prd_node(p) for p in plan.get("prds", [])]
        return {
            "name": plan["title"],
            "description": plan.get("description") or plan.get("vision") or "",
            "_type": "plan",
            "_url": f"{BASE_PATH}/plans/{plan['id']}",
            "_status": plan.get("status", "active"),
            "expanded": True,
            "children": children if children else None,
        }

    def project_node(project):
        plans = plans_by_project.get(project["id"], [])
        children = [plan_node(p) for p in plans]
        return {
            "name": project["title"],
            "description": project.get("description") or "",
            "_type": "project",
            "_url": f"{BASE_PATH}/projects/{project['id']}",
            "_status": project.get("status", "active"),
            "_priority": project.get("priority"),
            "expanded": True,
            "children": children if children else None,
        }

    root_children = [project_node(p) for p in projects]

    # Orphan plans
    orphan_plans = plans_by_project.get(None, [])
    if orphan_plans:
        root_children.append({
            "name": "Unlinked Plans",
            "_type": "section",
            "expanded": False,
            "children": [plan_node(p) for p in orphan_plans],
        })

    # Orphan PRDs
    orphan_prds = prds_by_plan.get(None, [])
    if orphan_prds:
        root_children.append({
            "name": "Unlinked PRDs",
            "_type": "section",
            "expanded": False,
            "children": [prd_node(p) for p in orphan_prds],
        })

    return {
        "name": "ProductAI",
        "_type": "root",
        "_url": f"{BASE_PATH}/",
        "expanded": True,
        "children": root_children if root_children else None,
    }


# ── Analytics ─────────────────────────────────────────

PRD_TEXT_FIELDS = [
    "content", "overview", "problem_statement", "proposed_solution",
    "timeline", "user_stories", "requirements_functional",
    "requirements_nonfunctional", "success_metrics",
]


@router.get("/analytics/prd-complexity")
async def prd_complexity():
    """Return all PRDs with per-field character counts, sorted by total size."""
    prds = await models.list_prds()
    result = []
    for prd in prds:
        fields = {}
        total = 0
        for f in PRD_TEXT_FIELDS:
            size = len(prd.get(f) or "")
            fields[f] = size
            total += size
        result.append({
            "id": prd["id"],
            "title": prd.get("title") or "(Untitled)",
            "status": prd.get("status") or "draft",
            "plan_id": prd.get("plan_id"),
            "total_size": total,
            "fields": fields,
        })
    result.sort(key=lambda x: x["total_size"], reverse=True)
    return result
