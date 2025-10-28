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
from fastapi import Request
import re
from typing import List
from fastapi import Query, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db import get_session
from app.models import Ingredient, Recipe, recipe_ingredient
from app.api import _map_input_to_ingredient_names

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

@app.get("/search", include_in_schema=False, name="search")
async def search(request: Request,
                 ingredients: str | None = Query(None),
                 limit: int | None = Query(20),
                 session: AsyncSession = Depends(get_session)):
    raw = ingredients or ""
    user_inputs = [s.strip() for s in re.split(r'[,\\n]+', raw) if s.strip()]

    recipes_out: List[dict] = []
    if user_inputs:
        mapped_names = await _map_input_to_ingredient_names(session, user_inputs)
        if mapped_names:
            stmt = (
                select(Recipe)
                .join(recipe_ingredient)
                .where(recipe_ingredient.c.ingredient_id.in_(
                    select(Ingredient.id).where(Ingredient.name.in_(mapped_names))
                ))
            )
            result = await session.execute(stmt)
            candidates = result.scalars().unique().all()

            for rec in candidates:
                ing_stmt = select(Ingredient.name).select_from(recipe_ingredient.join(Ingredient)).where(recipe_ingredient.c.recipe_id == rec.id)
                ing_res = await session.execute(ing_stmt)
                rec_ing_names = [row[0] for row in ing_res.fetchall()]

                user_norm = [u.lower() for u in mapped_names]
                have = sorted([i for i in rec_ing_names if i.lower() in user_norm])
                missing = sorted([i for i in rec_ing_names if i.lower() not in user_norm])
                match_count = len(have)
                total = max(len(rec_ing_names), 1)
                score = round(match_count / total, 3)

                recipes_out.append({
                    "id": rec.id,
                    "title": rec.title,
                    "score": score,
                    "match_count": match_count,
                    "missing": missing,
                    "have": have,
                    "ingredients": rec_ing_names,
                    "instructions": rec.instructions,
                    "prep_minutes": rec.prep_minutes,
                    "servings": rec.servings,
                    "image_url": rec.image_url,
                    "thumbnail_url": rec.thumbnail_url,
                    "image_meta": rec.image_meta,
                    "source": rec.source,
                })

            recipes_out = sorted(recipes_out, key=lambda x: (-x["score"], -x["match_count"], x["title"]))
            recipes_out = recipes_out[: max(1, min(100, int(limit or 20)))]

    return templates.TemplateResponse("search.html", {"request": request, "recipes": recipes_out})



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
