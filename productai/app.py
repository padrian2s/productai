"""ProductAI — AI-powered Product Management Service."""

import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .db.schema import init_db
from .routes.pages import router as pages_router
from .routes.api import router as api_router

BASE_PATH = os.environ.get("BASE_PATH", "").rstrip("/")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="ProductAI",
    description="AI-powered Product Management Service",
    root_path=BASE_PATH,
    lifespan=lifespan,
)

# Static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Routes
app.include_router(api_router)
app.include_router(pages_router)
