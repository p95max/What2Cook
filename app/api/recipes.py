import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert, func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from fastapi import APIRouter, Request, Response, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.models.anon import AnonUser, RecipeAction
from app.db import get_session
from app.schemas import RecipeSearchOut
from app.services.recipes import list_recipes, get_recipe, search_recipes
from app.utils.mapping import map_input_to_ingredient_names
from app.models import Recipe, Ingredient
from app.models.anon import RecipeAction
from app.deps import get_or_create_anon_user
import logging

router = APIRouter(prefix="/recipes", tags=["recipes"])

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

@router.get("/bookmarks", response_model=list)
async def api_get_bookmarks(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
):
    """
    Return list of bookmarked recipes for current anon user.
    """
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


logger = logging.getLogger(__name__)

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
    except Exception as e:
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

