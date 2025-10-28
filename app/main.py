"""
Main FastAPI application for What2Cook with simple HTML frontend.
"""
import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api import router as api_router
from app.db import init_db
from jinja2 import FileSystemLoader

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

try:
    templates.env.auto_reload = True
    templates.env.loader = FileSystemLoader(str(BASE_DIR / "templates"))
    templates.env.cache = {}
except Exception:
    pass

app = FastAPI(title="What2Cook", version="0.1.0")
app.include_router(api_router, prefix="/api")

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

@app.on_event("startup")
async def on_startup() -> None:
    if os.getenv("AUTO_INIT_DB", "true").lower() in ("1", "true", "yes"):
        await init_db()

@app.get("/search", include_in_schema=False)
async def search(request: Request):
    return templates.TemplateResponse("search.html", {"request": request})
