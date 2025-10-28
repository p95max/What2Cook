"""
Main FastAPI application for What2Cook with simple HTML frontend.
"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api import router as api_router
from app.db import init_db
from jinja2 import FileSystemLoader
from app import templates
from fastapi import Request, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.models import Recipe

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
async def search(request: Request, session: AsyncSession = Depends(get_session)):
    recipes = []
    return templates.TemplateResponse("search.html", {"request": request, "recipes": recipes})

@app.get("/recipes/{recipe_id}", include_in_schema=False, name="recipe_page")
async def recipe_page(request: Request, recipe_id: int, session: AsyncSession = Depends(get_session)):
    stmt = select(Recipe).options(selectinload(Recipe.ingredients)).where(Recipe.id == recipe_id)
    res = await session.execute(stmt)
    rec = res.scalars().first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recipe not found")

    recipe = {
        "id": rec.id,
        "title": rec.title,
        "instructions": rec.instructions,
        "prep_minutes": rec.prep_minutes,
        "servings": rec.servings,
        "source": rec.source,
        "image_url": rec.image_url,
        "thumbnail_url": rec.thumbnail_url,
        "image_meta": rec.image_meta,
        "ingredients": [ing.name for ing in rec.ingredients] if getattr(rec, "ingredients", None) else []
    }

    return templates.TemplateResponse("recipe_detail_page.html", {"request": request, "recipe": recipe})
