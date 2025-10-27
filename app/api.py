"""
API router for recipe search.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import AsyncSessionLocal
from app.models import Recipe, Ingredient, recipe_ingredient
from app.utils.normalize import normalize_ingredients_list
from app.utils.search import score_recipe

router = APIRouter()

class SearchRequest(BaseModel):
    ingredients: List[str]

class RecipeOut(BaseModel):
    id: int
    title: str
    score: float
    match_count: int
    missing: List[str]

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as s:
        yield s

@router.post("/recipes/search", response_model=List[RecipeOut])
async def search(req: SearchRequest, session: AsyncSession = Depends(get_session)):
    user_norm = normalize_ingredients_list(req.ingredients)
    stmt = select(Ingredient).where(Ingredient.name.in_(user_norm))
    result = await session.execute(stmt)
    found = result.scalars().all()
    user_ids = [i.id for i in found]
    if not user_ids:
        return []
    join_stmt = select(Recipe).join(recipe_ingredient).where(recipe_ingredient.c.ingredient_id.in_(user_ids)).distinct()
    res = await session.execute(join_stmt)
    candidates = res.scalars().all()
    out = []
    for r in candidates:
        rec_ing_stmt = select(Ingredient.name).select_from(recipe_ingredient.join(Ingredient)).where(recipe_ingredient.c.recipe_id == r.id)
        ing_res = await session.execute(rec_ing_stmt)
        rec_ing_names = [n for (n,) in ing_res.fetchall()]
        sc = score_recipe(rec_ing_names, user_norm)
        out.append({"id": r.id, "title": r.title, "score": sc["score"], "match_count": sc["match_count"], "missing": sc["missing"]})
    out_sorted = sorted(out, key=lambda x: (-x["score"], -x["match_count"]))
    return out_sorted[:50]
