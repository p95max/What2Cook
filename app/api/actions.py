from fastapi import APIRouter, Depends, Request, Response, HTTPException
from sqlalchemy import insert, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.deps import get_or_create_anon_user
from app.models.anon import RecipeAction
from app.models import Recipe

router = APIRouter(prefix="/api/recipes", tags=["recipes.actions"])


@router.post("/{recipe_id}/like", response_model=dict)
async def toggle_like(recipe_id: int, request: Request, response: Response, session: AsyncSession = Depends(get_session)):
    q = await session.execute(select(Recipe).where(Recipe.id == recipe_id))
    if not q.scalars().first():
        raise HTTPException(status_code=404, detail="Recipe not found")

    anon = await get_or_create_anon_user(request, response, session)
    try:
        await session.execute(insert(RecipeAction).values(
            anon_user_id=anon.id, recipe_id=recipe_id, action_type="like"
        ))
        await session.commit()
        return {"status": "liked"}
    except IntegrityError:
        await session.rollback()
        await session.execute(delete(RecipeAction).where(
            RecipeAction.anon_user_id == anon.id,
            RecipeAction.recipe_id == recipe_id,
            RecipeAction.action_type == "like"
        ))
        await session.commit()
        return {"status": "unliked"}


@router.post("/{recipe_id}/bookmark", response_model=dict)
async def toggle_bookmark(recipe_id: int, request: Request, response: Response, session: AsyncSession = Depends(get_session)):
    q = await session.execute(select(Recipe).where(Recipe.id == recipe_id))
    if not q.scalars().first():
        raise HTTPException(status_code=404, detail="Recipe not found")

    anon = await get_or_create_anon_user(request, response, session)
    try:
        await session.execute(insert(RecipeAction).values(
            anon_user_id=anon.id, recipe_id=recipe_id, action_type="bookmark"
        ))
        await session.commit()
        return {"status": "bookmarked"}
    except IntegrityError:
        await session.rollback()

        await session.execute(delete(RecipeAction).where(
            RecipeAction.anon_user_id == anon.id,
            RecipeAction.recipe_id == recipe_id,
            RecipeAction.action_type == "bookmark"
        ))
        await session.commit()
        return {"status": "unbookmarked"}
