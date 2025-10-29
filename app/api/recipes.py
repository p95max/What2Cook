import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas import RecipeSearchOut
from app.services.recipes import list_recipes, get_recipe, search_recipes
from app.utils.mapping import map_input_to_ingredient_names

router = APIRouter(prefix="/api/recipes", tags=["recipes"])

_SPLIT_RE = re.compile(r'[,\\n]+')


@router.get("/", response_model=dict)
async def api_list(page: int = Query(1, ge=1), session: AsyncSession = Depends(get_session)):
    """
    Return paginated recipes metadata (uses service layer).
    Response is a dict with keys: recipes, page, total_pages, per_page, total
    """
    return await list_recipes(session, page=page)


@router.get("/{recipe_id}", response_model=dict)
async def api_get(recipe_id: int, session: AsyncSession = Depends(get_session)):
    """
    Return a single recipe dict or 404.
    """
    recipe = await get_recipe(session, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.get("/search", response_model=List[RecipeSearchOut])
async def api_search(
    ingredients: Optional[str] = Query(None, description="Comma- or newline-separated ingredient names"),
    limit: Optional[int] = Query(20, ge=1, le=100),
    page: Optional[int] = Query(1, ge=1),
    min_score: Optional[float] = Query(0.0, ge=0.0, le=1.0),
    session: AsyncSession = Depends(get_session),
):
    """
    Search recipes by a free-text ingredients list.

    - `ingredients` must be provided (comma or newline separated).
    - `map_input_to_ingredient_names` maps user inputs to canonical DB ingredient names.
    - Results come from service.search_recipes and are filtered by min_score and paginated here.
    """
    raw = (ingredients or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="ingredients must be provided")

    user_inputs = [s.strip() for s in _SPLIT_RE.split(raw) if s.strip()]
    if not user_inputs:
        raise HTTPException(status_code=400, detail="no valid ingredient tokens found")

    if len(user_inputs) > 50:
        raise HTTPException(status_code=400, detail="too many ingredients (max 50)")

    mapped = await map_input_to_ingredient_names(session, user_inputs)
    if not mapped:
        return []

    results = await search_recipes(session=session, mapped_names=mapped, limit=1000)  # get large set, paginate below

    if min_score and min_score > 0.0:
        results = [r for r in results if float(r.get("score", 0.0)) >= float(min_score)]

    results.sort(key=lambda x: (-x.get("score", 0.0), -x.get("match_count", 0), x.get("title", "")))

    per_page = max(1, min(100, int(limit or 20)))
    page_num = max(1, int(page or 1))
    start = (page_num - 1) * per_page
    end = start + per_page
    return results[start:end]
