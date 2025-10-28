"""
CRUD helpers for recipes and ingredients.
"""
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Recipe, Ingredient

async def find_recipes_by_ingredient_ids(session: AsyncSession, ingredient_ids: list[int]) -> list[Recipe]:
    stmt = select(Recipe).options(selectinload(Recipe.ingredients)).join(Recipe.ingredients).where(Ingredient.id.in_(ingredient_ids))
    result = await session.execute(stmt)
    return result.scalars().unique().all()
