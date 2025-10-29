# app/api/recipes.py
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert, func
from sqlalchemy.exc import IntegrityError

from app.db import get_session
from app.schemas import RecipeSearchOut
from app.services.recipes import list_recipes, get_recipe, search_recipes
from app.utils.mapping import map_input_to_ingredient_names

# models for actions
from app.models import Recipe, Ingredient  # ensure Recipe is available for existence checks
# direct import for RecipeAction model (created earlier)
from app.models.anon import RecipeAction

# dependency helper to create/get anon user
from app.deps import get_or_create_anon_user

router = APIRouter(prefix="/recipes", tags=["recipes"])  # note: prefix "/recipes" — main includes router under /api

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


# ----------------- Anonymous actions endpoints -----------------

@router.get("/{recipe_id}/actions", response_model=dict)
async def recipe_actions(
    recipe_id: int,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    """
    Return actions state for current anon user and global likes_count:
    { liked: bool, bookmarked: bool, likes_count: int }
    """
    q = await session.execute(select(Recipe).where(Recipe.id == recipe_id))
    if not q.scalars().first():
        raise HTTPException(status_code=404, detail="Recipe not found")

    anon = await get_or_create_anon_user(request, response, session)

    # liked?
    q = await session.execute(
        select(RecipeAction).where(
            RecipeAction.anon_user_id == anon.id,
            RecipeAction.recipe_id == recipe_id,
            RecipeAction.action_type == "like",
        )
    )
    liked = q.scalars().first() is not None

    q2 = await session.execute(
        select(RecipeAction).where(
            RecipeAction.anon_user_id == anon.id,
            RecipeAction.recipe_id == recipe_id,
            RecipeAction.action_type == "bookmark",
        )
    )
    bookmarked = q2.scalars().first() is not None

    cnt_q = await session.execute(
        select(func.count()).select_from(RecipeAction).where(
            RecipeAction.recipe_id == recipe_id, RecipeAction.action_type == "like"
        )
    )
    likes_count = int(cnt_q.scalar_one() or 0)

    return {"liked": liked, "bookmarked": bookmarked, "likes_count": likes_count}


@router.post("/{recipe_id}/like", response_model=dict)
async def toggle_like(
    recipe_id: int,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    """
    Toggle like for current anon user.
    Returns {"status":"liked"} or {"status":"unliked"}.
    """
    q = await session.execute(select(Recipe).where(Recipe.id == recipe_id))
    if not q.scalars().first():
        raise HTTPException(status_code=404, detail="Recipe not found")

    anon = await get_or_create_anon_user(request, response, session)

    q = await session.execute(
        select(RecipeAction).where(
            RecipeAction.anon_user_id == anon.id,
            RecipeAction.recipe_id == recipe_id,
            RecipeAction.action_type == "like",
        )
    )
    existing = q.scalars().first()
    if existing:
        await session.execute(delete(RecipeAction).where(RecipeAction.id == existing.id))
        await session.commit()
        return {"status": "unliked"}

    try:
        stmt = insert(RecipeAction).values(
            anon_user_id=anon.id, recipe_id=recipe_id, action_type="like"
        )
        await session.execute(stmt)
        await session.commit()
        return {"status": "liked"}
    except IntegrityError:
        await session.rollback()
        return {"status": "liked"}
