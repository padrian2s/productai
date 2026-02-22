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
