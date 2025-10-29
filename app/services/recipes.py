from typing import List, Dict, Optional
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import Recipe, Ingredient, recipe_ingredient

PER_PAGE = 9

async def list_recipes(session: AsyncSession, page: int = 1, per_page: int = PER_PAGE) -> Dict:
    offset = (page - 1) * per_page
    stmt = select(Recipe).options(selectinload(Recipe.ingredients)).order_by(Recipe.title).offset(offset).limit(per_page)
    res = await session.execute(stmt)
    recs = res.scalars().unique().all()
    total = (await session.execute(select(func.count()).select_from(Recipe))).scalar_one()
    total_pages = max(1, (int(total) + per_page - 1) // per_page)

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
            "likes_count": getattr(rec, "likes_count", 0)
        }

    return {
        "recipes": [to_out(r) for r in recs],
        "page": page,
        "total_pages": total_pages,
        "per_page": per_page,
        "total": int(total),
    }

async def get_recipe(session: AsyncSession, recipe_id: int) -> Optional[Dict]:
    stmt = select(Recipe).options(selectinload(Recipe.ingredients)).where(Recipe.id == recipe_id)
    res = await session.execute(stmt)
    rec = res.scalars().first()
    if not rec:
        return None
    return {
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
        "likes_count": getattr(rec, "likes_count", 0)
    }

async def search_recipes(session: AsyncSession, mapped_names: List[str], limit: int = 20) -> List[Dict]:
    if not mapped_names:
        return []
    ing_ids_subq = select(Ingredient.id).where(Ingredient.name.in_(mapped_names))
    stmt = (
        select(Recipe, func.count(recipe_ingredient.c.ingredient_id).label("match_count"))
        .join(recipe_ingredient, recipe_ingredient.c.recipe_id == Recipe.id)
        .where(recipe_ingredient.c.ingredient_id.in_(ing_ids_subq))
        .group_by(Recipe.id)
        .order_by(desc("match_count"), Recipe.title)
        .limit(max(1, min(100, int(limit or 20))))
    )
    res = await session.execute(stmt)
    rows = res.all()
    out = []
    for rec, match_count in rows:
        ing_stmt = select(Ingredient.name).select_from(recipe_ingredient.join(Ingredient)).where(recipe_ingredient.c.recipe_id == rec.id)
        ing_res = await session.execute(ing_stmt)
        rec_ing_names = [row[0] for row in ing_res.fetchall()]
        total = max(len(rec_ing_names), 1)
        score = round(match_count / total, 3)
        out.append({
            "id": rec.id,
            "title": rec.title,
            "score": score,
            "match_count": int(match_count),
            "missing": sorted([i for i in rec_ing_names if i.lower() not in [u.lower() for u in mapped_names]]),
            "have": sorted([i for i in rec_ing_names if i.lower() in [u.lower() for u in mapped_names]]),
            "ingredients": rec_ing_names,
            "instructions": rec.instructions,
            "prep_minutes": rec.prep_minutes,
            "servings": rec.servings,
            "image_url": rec.image_url,
            "thumbnail_url": rec.thumbnail_url,
            "image_meta": rec.image_meta,
            "source": rec.source,
        })
    return out
