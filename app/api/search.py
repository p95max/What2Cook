import re
import logging
from typing import List, Optional, Set
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from app.db import get_session
from app.models import Recipe, Ingredient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recipes", tags=["recipes.search"])

_SPLIT_RE = re.compile(r'[,\n]+')

@router.get("/ingredients")
async def api_ingredients(
    q: Optional[str] = Query(None, description="Prefix filter (case-insensitive)"),
    limit: int = Query(1000, ge=1, le=5000),
    session: AsyncSession = Depends(get_session),
):
    """
    Return list of ingredient names (strings). Uses GROUP BY to be Postgres-friendly
    when ordering by lower(name).
    """
    stmt = select(Ingredient.name).group_by(Ingredient.name)
    if q:
        stmt = stmt.where(func.lower(Ingredient.name).like(f"{q.lower()}%"))
    stmt = stmt.order_by(func.lower(Ingredient.name)).limit(limit)

    res = await session.execute(stmt)
    names = [row[0] for row in res.fetchall() if row and row[0] is not None]
    return names


@router.get("/search_simple")
async def api_search_simple(
    ingredient: Optional[List[str]] = Query(None, description="Repeatable: ?ingredient=egg&ingredient=onion"),
    limit: int = Query(50, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    """
    Simple ingredient-based search. Matches recipes that contain ANY of the provided
    ingredients. Returns simple JSON objects used by frontend.
    """
    if not ingredient:
        raise HTTPException(status_code=400, detail="provide at least one ingredient query param (ingredient=...)")

    names = [s.strip() for s in ingredient if s and s.strip()]
    if not names:
        raise HTTPException(status_code=400, detail="no valid ingredient tokens found")

    lower_names: Set[str] = {n.lower() for n in names}

    any_conditions = [Recipe.ingredients.any(func.lower(Ingredient.name) == ln) for ln in lower_names]
    if not any_conditions:
        return []

    stmt = select(Recipe).options(selectinload(Recipe.ingredients)).where(or_(*any_conditions)).limit(2000)
    res = await session.execute(stmt)
    recipes = res.scalars().unique().all()

    out = []
    for rec in recipes:
        rec_ing_names = [getattr(i, "name", "").lower() for i in getattr(rec, "ingredients", []) or []]
        match_count = len(set(rec_ing_names) & lower_names)
        total_ing = len(rec_ing_names) or 1
        score = match_count / total_ing
        out.append({
            "id": rec.id,
            "title": rec.title,
            "instructions": rec.instructions,
            "prep_minutes": rec.prep_minutes,
            "servings": rec.servings,
            "source": rec.source,
            "image_url": rec.image_url,
            "thumbnail_url": rec.thumbnail_url,
            "image_meta": rec.image_meta,
            "ingredients": [ing.name for ing in getattr(rec, "ingredients", [])] if getattr(rec, "ingredients", None) else [],
            "likes_count": getattr(rec, "likes_count", 0),
            "match_count": match_count,
            "score": score,
        })

    out.sort(key=lambda x: (-x["match_count"], -x["score"], x["title"]))
    return out[:limit]
