"""Page routes — serve HTML templates."""

import json
import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from ..db import models

BASE_PATH = os.environ.get("BASE_PATH", "").rstrip("/")

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")
templates.env.globals["base_path"] = BASE_PATH


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    projects = await models.list_projects()
    all_plans = await models.list_plans()
    all_prds = await models.list_prds()

    # Index PRDs by plan_id
    prds_by_plan: dict[int | None, list[dict]] = {}
    for prd in all_prds:
        prd["version"] = await models.get_current_version_number("prd", prd["id"])
        prds_by_plan.setdefault(prd.get("plan_id"), []).append(prd)

    # Index plans by project_id, attach their PRDs
    plans_by_project: dict[int | None, list[dict]] = {}
    for plan in all_plans:
        plan["version"] = await models.get_current_version_number("plan", plan["id"])
        plan["prds"] = prds_by_plan.get(plan["id"], [])
        plans_by_project.setdefault(plan.get("project_id"), []).append(plan)

    # Attach plans (with nested PRDs) to each project
    for project in projects:
        project["version"] = await models.get_current_version_number("project", project["id"])
        project["plans"] = plans_by_project.get(project["id"], [])

    # Orphan plans/PRDs (not linked to any project)
    orphan_plans = plans_by_project.get(None, [])
    orphan_prds = prds_by_plan.get(None, [])

    return templates.TemplateResponse(
        "pages/dashboard.html",
        {
            "request": request,
            "projects": projects,
            "orphan_plans": orphan_plans,
            "orphan_prds": orphan_prds,
        },
    )


# ── Projects ──────────────────────────────────────────

@router.get("/projects/new", response_class=HTMLResponse)
async def new_project_page(request: Request):
    return templates.TemplateResponse(
        "pages/project_edit.html",
        {"request": request, "project": None},
    )


@router.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_detail(request: Request, project_id: int):
    project = await models.get_project(project_id)
    if not project:
        return HTMLResponse("<h1>Project not found</h1>", status_code=404)
    plans = await models.list_plans(project_id=project_id)
    # Gather PRDs for all linked plans
    prds = []
    for plan in plans:
        plan_prds = await models.list_prds(plan_id=plan["id"])
        prds.extend(plan_prds)
    current_version = await models.get_current_version_number("project", project_id)
    return templates.TemplateResponse(
        "pages/project_detail.html",
        {"request": request, "project": project, "plans": plans, "prds": prds, "current_version": current_version},
    )


@router.get("/projects/{project_id}/edit", response_class=HTMLResponse)
async def edit_project_page(request: Request, project_id: int):
    project = await models.get_project(project_id)
    if not project:
        return HTMLResponse("<h1>Project not found</h1>", status_code=404)
    current_version = await models.get_current_version_number("project", project_id)
    return templates.TemplateResponse(
        "pages/project_edit.html",
        {"request": request, "project": project, "current_version": current_version},
    )


@router.get("/projects/{project_id}/versions", response_class=HTMLResponse)
async def project_versions_page(request: Request, project_id: int):
    project = await models.get_project(project_id)
    if not project:
        return HTMLResponse("<h1>Project not found</h1>", status_code=404)
    versions = await models.list_versions("project", project_id)
    current_version = await models.get_current_version_number("project", project_id)
    return templates.TemplateResponse(
        "pages/versions.html",
        {
            "request": request,
            "entity": project,
            "entity_type": "project",
            "versions": versions,
            "current_version": current_version,
        },
    )


# ── Plans ─────────────────────────────────────────────

@router.get("/plans/new", response_class=HTMLResponse)
async def new_plan_page(request: Request):
    projects = await models.list_projects()
    return templates.TemplateResponse(
        "pages/plan_edit.html",
        {"request": request, "plan": None, "projects": projects},
    )


@router.get("/plans/{plan_id}", response_class=HTMLResponse)
async def plan_detail(request: Request, plan_id: int):
    plan = await models.get_plan(plan_id)
    if not plan:
        return HTMLResponse("<h1>Plan not found</h1>", status_code=404)
    project = await models.get_project(plan["project_id"]) if plan.get("project_id") else None
    prds = await models.list_prds(plan_id=plan_id)
    current_version = await models.get_current_version_number("plan", plan_id)
    return templates.TemplateResponse(
        "pages/plan_detail.html",
        {"request": request, "plan": plan, "project": project, "prds": prds, "current_version": current_version},
    )


@router.get("/plans/{plan_id}/edit", response_class=HTMLResponse)
async def edit_plan_page(request: Request, plan_id: int):
    plan = await models.get_plan(plan_id)
    if not plan:
        return HTMLResponse("<h1>Plan not found</h1>", status_code=404)
    projects = await models.list_projects()
    current_version = await models.get_current_version_number("plan", plan_id)
    return templates.TemplateResponse(
        "pages/plan_edit.html",
        {"request": request, "plan": plan, "projects": projects, "current_version": current_version},
    )


@router.get("/plans/{plan_id}/chat", response_class=HTMLResponse)
async def plan_chat_page(request: Request, plan_id: int):
    plan = await models.get_plan(plan_id)
    if not plan:
        return HTMLResponse("<h1>Plan not found</h1>", status_code=404)
    session = await models.get_or_create_session("plan", plan_id)
    return templates.TemplateResponse(
        "pages/plan_chat.html",
        {"request": request, "plan": plan, "session": session},
    )


@router.get("/prds/new", response_class=HTMLResponse)
async def new_prd_page(request: Request):
    plans = await models.list_plans()
    return templates.TemplateResponse(
        "pages/prd_edit.html",
        {"request": request, "prd": None, "plans": plans},
    )


@router.get("/prds/{prd_id}", response_class=HTMLResponse)
async def prd_detail(request: Request, prd_id: int):
    prd = await models.get_prd(prd_id)
    if not prd:
        return HTMLResponse("<h1>PRD not found</h1>", status_code=404)
    plan = await models.get_plan(prd["plan_id"]) if prd["plan_id"] else None
    current_version = await models.get_current_version_number("prd", prd_id)
    return templates.TemplateResponse(
        "pages/prd_detail.html",
        {"request": request, "prd": prd, "plan": plan, "current_version": current_version},
    )


@router.get("/prds/{prd_id}/edit", response_class=HTMLResponse)
async def edit_prd_page(request: Request, prd_id: int):
    prd = await models.get_prd(prd_id)
    if not prd:
        return HTMLResponse("<h1>PRD not found</h1>", status_code=404)
    plans = await models.list_plans()
    current_version = await models.get_current_version_number("prd", prd_id)
    return templates.TemplateResponse(
        "pages/prd_edit.html",
        {"request": request, "prd": prd, "plans": plans, "current_version": current_version},
    )


@router.get("/prds/{prd_id}/chat", response_class=HTMLResponse)
async def prd_chat_page(request: Request, prd_id: int):
    prd = await models.get_prd(prd_id)
    if not prd:
        return HTMLResponse("<h1>PRD not found</h1>", status_code=404)
    session = await models.get_or_create_session("prd", prd_id)
    return templates.TemplateResponse(
        "pages/prd_chat.html",
        {"request": request, "prd": prd, "session": session},
    )


# ── Admin ──────────────────────────────────────────────

@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    settings = await models.get_all_settings()
    has_env_key = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
    return templates.TemplateResponse(
        "pages/admin.html",
        {"request": request, "settings": settings, "has_env_key": has_env_key},
    )


# ── Version History ────────────────────────────────────

@router.get("/plans/{plan_id}/versions", response_class=HTMLResponse)
async def plan_versions_page(request: Request, plan_id: int):
    plan = await models.get_plan(plan_id)
    if not plan:
        return HTMLResponse("<h1>Plan not found</h1>", status_code=404)
    versions = await models.list_versions("plan", plan_id)
    current_version = await models.get_current_version_number("plan", plan_id)
    return templates.TemplateResponse(
        "pages/versions.html",
        {
            "request": request,
            "entity": plan,
            "entity_type": "plan",
            "versions": versions,
            "current_version": current_version,
        },
    )


@router.get("/prds/{prd_id}/versions", response_class=HTMLResponse)
async def prd_versions_page(request: Request, prd_id: int):
    prd = await models.get_prd(prd_id)
    if not prd:
        return HTMLResponse("<h1>PRD not found</h1>", status_code=404)
    versions = await models.list_versions("prd", prd_id)
    current_version = await models.get_current_version_number("prd", prd_id)
    return templates.TemplateResponse(
        "pages/versions.html",
        {
            "request": request,
            "entity": prd,
            "entity_type": "prd",
            "versions": versions,
            "current_version": current_version,
        },
    )


@router.get("/versions/{version_id}", response_class=HTMLResponse)
async def version_snapshot_page(request: Request, version_id: int):
    version = await models.get_version(version_id)
    if not version:
        return HTMLResponse("<h1>Version not found</h1>", status_code=404)
    snapshot = json.loads(version["snapshot"])
    return templates.TemplateResponse(
        "pages/version_detail.html",
        {"request": request, "version": version, "snapshot": snapshot},
    )
