"""
API router exposing improved recipe search endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List
from app.db import get_session
from app.models import Ingredient, Recipe, recipe_ingredient
from app.schemas import IngredientsQuery, RecipeSearchOut
from app.utils.normalize import normalize_list, fuzzy_best_match

router = APIRouter()

async def _map_input_to_ingredient_names(session: AsyncSession, user_inputs: List[str]) -> List[str]:
    normalized = normalize_list(user_inputs)
    if not normalized:
        return []
    stmt = select(Ingredient)
    result = await session.execute(stmt)
    all_ings = result.scalars().all()
    name_to_obj = {normalize_list([ing.name])[0]: ing for ing in all_ings}
    for ing in all_ings:
        if ing.aliases:
            for a in ing.aliases:
                name_to_obj[normalize_list([a])[0]] = ing
    found_names = []
    available_choices = list(name_to_obj.keys())
    for n in normalized:
        if n in name_to_obj:
            found_names.append(name_to_obj[n].name)
            continue
        match, score = fuzzy_best_match(n, available_choices)
        if match and score >= 85:
            found_names.append(name_to_obj[match].name)
    return list(dict.fromkeys(found_names))

@router.post("/recipes/search", response_model=List[RecipeSearchOut])
async def search_recipes(query: IngredientsQuery, session: AsyncSession = Depends(get_session)):
    if not query.ingredients:
        raise HTTPException(status_code=400, detail="ingredients must be provided")

    user_ing_names = await _map_input_to_ingredient_names(session, query.ingredients)
    if not user_ing_names:
        return []

    ing_ids_subq = select(Ingredient.id).where(Ingredient.name.in_(user_ing_names))

    stmt = (
        select(
            Recipe,
            func.count(recipe_ingredient.c.ingredient_id).label("match_count")
        )
        .join(recipe_ingredient, recipe_ingredient.c.recipe_id == Recipe.id)
        .where(recipe_ingredient.c.ingredient_id.in_(ing_ids_subq))
        .group_by(Recipe.id)
        .order_by(desc("match_count"), Recipe.title)
    )

    result = await session.execute(stmt)
    rows = result.all()
    out = []
    for rec, match_count in rows:
        ing_stmt = select(Ingredient.name).select_from(recipe_ingredient.join(Ingredient)).where(recipe_ingredient.c.recipe_id == rec.id)
        ing_res = await session.execute(ing_stmt)
        rec_ing_names = [row[0] for row in ing_res.fetchall()]

        total = max(len(rec_ing_names), 1)
        score = round(match_count / total, 3)

        if score >= (query.min_score or 0.0):
            out.append({
                "id": rec.id,
                "title": rec.title,
                "score": score,
                "match_count": int(match_count),
                "missing": sorted([i for i in rec_ing_names if i.lower() not in [u.lower() for u in user_ing_names]]),
                "have": sorted([i for i in rec_ing_names if i.lower() in [u.lower() for u in user_ing_names]]),
                "ingredients": rec_ing_names,
                "instructions": rec.instructions,
                "prep_minutes": rec.prep_minutes,
                "servings": rec.servings,
                "image_url": rec.image_url,
                "thumbnail_url": rec.thumbnail_url,
                "image_meta": rec.image_meta,
                "source": rec.source,
            })

    out_sorted = sorted(out, key=lambda x: (-x["score"], -x["match_count"], x["title"]))
    limit = max(1, min(100, query.limit or 20))
    page = max(1, query.page or 1)
    start = (page - 1) * limit
    return out_sorted[start:start+limit]
