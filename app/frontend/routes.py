import re
from fastapi import APIRouter, Depends, Query
from fastapi.templating import Jinja2Templates
from app.db import get_session
from app.models import Recipe, Ingredient
from app.services.recipes import list_recipes, get_recipe, search_recipes
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.mapping import map_input_to_ingredient_names
from fastapi import Request, Response
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models.anon import RecipeAction
from app.deps import get_or_create_anon_user

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
    """
    Render search page. If no `ingredients` query param — load and show all available ingredients.
    If `ingredients` provided (comma- or newline-separated) perform search and show recipes.
    """
    stmt = select(Ingredient.name).order_by(func.lower(Ingredient.name)).limit(2000)
    res = await session.execute(stmt)
    available_ings = [row[0] for row in res.all() if row and row[0] is not None]

    raw = ingredients or ""
    user_inputs = [s.strip() for s in re.split(r'[,\\n]+', raw) if s.strip()]
    if not user_inputs:
        return templates.TemplateResponse("search.html", {"request": request, "ingredients": available_ings})

    mapped_names = await map_input_to_ingredient_names(session, user_inputs)
    recipes = await search_recipes(session, mapped_names, limit=int(limit or 20))
    return templates.TemplateResponse("search.html", {"request": request, "recipes": recipes, "ingredients": available_ings})

@router.get("/bookmarks", include_in_schema=False, name="bookmarks")
async def bookmarks_page(request: Request, response: Response, session: AsyncSession = Depends(get_session)):
    """
    Render page with recipes that the current anon user bookmarked.
    """
    anon = await get_or_create_anon_user(request, response, session)

    stmt = (
        select(Recipe)
        .join(RecipeAction, RecipeAction.recipe_id == Recipe.id)
        .where(
            RecipeAction.anon_user_id == anon.id,
            RecipeAction.action_type == "bookmark",
        )
        .options(selectinload(Recipe.ingredients))
        .order_by(RecipeAction.created_at.desc())
    )
    res = await session.execute(stmt)
    recs = res.scalars().unique().all()

    def to_out(rec):
        return {
            "id": rec.id,
            "title": rec.title,
            "instructions": rec.instructions,
            "prep_minutes": rec.prep_minutes,
            "servings": rec.servings,
            "image_url": rec.image_url,
            "thumbnail_url": rec.thumbnail_url,
            "image_meta": rec.image_meta,
            "ingredients": [ing.name for ing in getattr(rec, "ingredients", [])] if getattr(rec, "ingredients", None) else [],
            "likes_count": getattr(rec, "likes_count", 0),
        }

    ctx = {"request": request, "recipes": [to_out(r) for r in recs]}
    return templates.TemplateResponse("bookmarks.html", ctx)