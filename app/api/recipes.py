import re
import logging
from typing import List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert, func, update, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.db import get_session
from app.models import Recipe, Ingredient
from app.models.anon import AnonUser, RecipeAction
from app.schemas import RecipeSearchOut
from app.services.recipes import list_recipes, get_recipe
from app.deps import get_or_create_anon_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["recipes"])

_SPLIT_RE = re.compile(r'[,\n]+')


# ---------- simplified search / ingredients endpoints (static routes) ----------

@router.get("/ingredients")
async def api_ingredients(
    q: Optional[str] = Query(None, description="Prefix filter (case-insensitive)"),
    limit: int = Query(1000, ge=1, le=5000),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Ingredient.name)
    if q:
        stmt = stmt.where(func.lower(Ingredient.name).like(f"{q.lower()}%"))
    stmt = stmt.order_by(func.lower(Ingredient.name)).limit(limit)

    res = await session.execute(stmt)
    names = [row[0] for row in res.all() if row and row[0] is not None]
    return names



@router.get("/search_simple")
async def api_search_simple(
    ingredient: Optional[List[str]] = Query(None, description="Repeatable: ?ingredient=egg&ingredient=onion"),
    limit: int = Query(50, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    if not ingredient:
        raise HTTPException(status_code=400, detail="provide at least one ingredient query param (ingredient=...)")

    names = [s.strip() for s in ingredient if s and s.strip()]
    if not names:
        raise HTTPException(status_code=400, detail="no valid ingredient tokens found")

    lower_names: Set[str] = {n.lower() for n in names}

    any_conditions = [Recipe.ingredients.any(func.lower(Ingredient.name) == ln) for ln in lower_names]
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


# ---------- existing collection endpoints ----------

@router.get("/", response_model=dict)
async def api_list(page: int = Query(1, ge=1), session: AsyncSession = Depends(get_session)):
    return await list_recipes(session, page=page)


@router.get("/bookmarks", response_model=list)
async def api_get_bookmarks(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
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
    recipes = res.scalars().unique().all()

    def to_out(rec):
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
            "likes_count": getattr(rec, "likes_count", 0),
        }

    return [to_out(r) for r in recipes]


@router.post("/clear", response_model=dict)
async def clear_anon_data(request: Request, response: Response, session: AsyncSession = Depends(get_session)):
    if request.headers.get("X-Requested-With") != "XMLHttpRequest":
        raise HTTPException(status_code=400, detail="Bad request")

    anon_cookie = request.cookies.get("anon_id")
    if not anon_cookie:
        response.status_code = 204
        return {"status": "no_anon"}

    try:
        cols = {c.name for c in AnonUser.__table__.columns}
    except Exception:
        logger.exception("Failed to introspect AnonUser.__table__")
        cols = set()

    logger.debug("AnonUser columns: %s", sorted(cols))

    anon = None

    if "id" in cols:
        try:
            maybe_id = int(anon_cookie)
            q = await session.execute(select(AnonUser).where(AnonUser.id == maybe_id))
            anon = q.scalars().first()
            if anon:
                logger.info("Found AnonUser by numeric id column")
        except Exception:
            pass

    if not anon:
        candidates = [
            "anon_id", "anon_token", "token", "token_value", "token_hash",
            "cookie", "cookie_value", "uuid", "uid", "key", "value", "secret"
        ]
        for name in candidates:
            if name in cols and hasattr(AnonUser, name):
                try:
                    col = getattr(AnonUser, name)
                    q = await session.execute(select(AnonUser).where(col == anon_cookie))
                    anon = q.scalars().first()
                    if anon:
                        logger.info("Found AnonUser by column '%s'", name)
                        break
                except Exception:
                    logger.debug("Failed query by candidate column %s", name, exc_info=True)

    if not anon:
        for colname in cols:
            if colname == "id":
                continue
            if not hasattr(AnonUser, colname):
                continue
            try:
                col = getattr(AnonUser, colname)
                q = await session.execute(select(AnonUser).where(col == anon_cookie))
                anon = q.scalars().first()
                if anon:
                    logger.info("Found AnonUser by fallback column '%s'", colname)
                    break
            except Exception:
                continue

    if not anon:
        logger.info("AnonUser not found for cookie value; available columns: %s", sorted(cols))
        response.delete_cookie("anon_id", path="/", samesite="Lax")
        response.status_code = 204
        return {"status": "no_anon", "available_columns": sorted(cols)}

    try:
        await session.execute(delete(RecipeAction).where(RecipeAction.anon_user_id == anon.id))
        await session.execute(delete(AnonUser).where(AnonUser.id == anon.id))
        await session.commit()
    except Exception:
        await session.rollback()
        logger.exception("Failed to delete AnonUser and RecipeAction for anon id %s", getattr(anon, "id", "<unknown>"))
        raise HTTPException(status_code=500, detail="Unable to delete anon data")

    response.delete_cookie("anon_id", path="/", samesite="Lax")
    return {"status": "deleted"}


# ---------- recipe-specific dynamic endpoints (must come after static routes) ----------

@router.get("/{recipe_id}/actions", response_model=dict)
async def recipe_actions(
    recipe_id: int,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
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
        cnt_q = await session.execute(select(func.count()).select_from(RecipeAction).where(RecipeAction.recipe_id == recipe_id, RecipeAction.action_type == "like"))
        likes_count = int(cnt_q.scalar_one() or 0)
        await session.execute(update(Recipe).where(Recipe.id == recipe_id).values(likes_count=likes_count))
        await session.commit()
        return {"status": "unliked", "likes_count": likes_count}

    try:
        await session.execute(insert(RecipeAction).values(anon_user_id=anon.id, recipe_id=recipe_id, action_type="like"))
        await session.commit()
    except IntegrityError:
        await session.rollback()

    cnt_q = await session.execute(select(func.count()).select_from(RecipeAction).where(RecipeAction.recipe_id == recipe_id, RecipeAction.action_type == "like"))
    likes_count = int(cnt_q.scalar_one() or 0)
    await session.execute(update(Recipe).where(Recipe.id == recipe_id).values(likes_count=likes_count))
    await session.commit()
    return {"status": "liked", "likes_count": likes_count}


@router.post("/{recipe_id}/bookmark", response_model=dict)
async def toggle_bookmark(
    recipe_id: int,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    q = await session.execute(select(Recipe).where(Recipe.id == recipe_id))
    if not q.scalars().first():
        raise HTTPException(status_code=404, detail="Recipe not found")

    anon = await get_or_create_anon_user(request, response, session)

    q = await session.execute(
        select(RecipeAction).where(
            RecipeAction.anon_user_id == anon.id,
            RecipeAction.recipe_id == recipe_id,
            RecipeAction.action_type == "bookmark",
        )
    )
    existing = q.scalars().first()
    if existing:
        await session.execute(delete(RecipeAction).where(RecipeAction.id == existing.id))
        await session.commit()
        return {"status": "unbookmarked"}
    try:
        await session.execute(insert(RecipeAction).values(anon_user_id=anon.id, recipe_id=recipe_id, action_type="bookmark"))
        await session.commit()
        return {"status": "bookmarked"}
    except IntegrityError:
        await session.rollback()
        return {"status": "bookmarked"}


@router.get("/{recipe_id}", response_model=dict)
async def api_get(recipe_id: int, session: AsyncSession = Depends(get_session)):
    recipe = await get_recipe(session, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe
