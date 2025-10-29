import re

from fastapi import APIRouter, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from app.db import get_session
from app.services.recipes import list_recipes, get_recipe, search_recipes
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.utils.mapping import map_input_to_ingredient_names

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
@router.get("/", include_in_schema=False, name="index")
async def index(request: Request, page: int = Query(1, ge=1), session: AsyncSession = Depends(get_session)):
    ctx = await list_recipes(session, page=page)
    ctx.update({"request": request})
    return templates.TemplateResponse("index.html", ctx)

@router.get("/recipes/{recipe_id}", include_in_schema=False, name="recipe_page")
async def recipe_page(request: Request, recipe_id: int, session: AsyncSession = Depends(get_session)):
    recipe = await get_recipe(session, recipe_id)
    if not recipe:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Recipe not found")
    return templates.TemplateResponse("recipe_detail_page.html", {"request": request, "recipe": recipe})

@router.get("/search", include_in_schema=False, name="search")
async def search(request: Request, ingredients: str | None = Query(None), limit: int | None = Query(20), session: AsyncSession = Depends(get_session)):
    raw = ingredients or ""
    user_inputs = [s.strip() for s in re.split(r'[,\\n]+', raw) if s.strip()]
    if not user_inputs:
        return templates.TemplateResponse("search.html", {"request": request})
    mapped_names = await map_input_to_ingredient_names(session, user_inputs)
    recipes = await search_recipes(session, mapped_names, limit=int(limit or 20))
    return templates.TemplateResponse("search.html", {"request": request, "recipes": recipes})
