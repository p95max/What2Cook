from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import insert, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import get_or_create_anon_user
from app.models.anon import RecipeAction

router = APIRouter(prefix="/api/recipes")

@router.post("/{recipe_id}/like", response_model=dict)
async def toggle_like(recipe_id: int, request: Request, response: Response, session: AsyncSession = Depends(get_session)):
    anon = await get_or_create_anon_user(request, response, session)
    try:
        await session.execute(insert(RecipeAction).values(anon_user_id=anon.id, recipe_id=recipe_id))
        await session.commit()

        return {"status": "liked"}
    except IntegrityError:
        await session.rollback()
        await session.execute(delete(RecipeAction).where(RecipeAction.anon_user_id==anon.id, RecipeAction.recipe_id==recipe_id))
        await session.commit()
        return {"status": "unliked"}
