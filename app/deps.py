import uuid
from fastapi import Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.anon import AnonUser
from app.db import get_session
from app.utils.anon_cookie import load_anon_cookie_val, make_anon_cookie_val

async def get_or_create_anon_user(request: Request, response: Response, session: AsyncSession):
    cookie = request.cookies.get("anon_id")
    anon_id = None
    if cookie:
        anon_id = load_anon_cookie_val(cookie)
    if anon_id:
        try:
            q = await session.execute(select(AnonUser).where(AnonUser.id == anon_id))
            user = q.scalars().first()
            if user:
                return user
        except Exception:
            pass

    new_id = uuid.uuid4()
    user = AnonUser(id=new_id)
    session.add(user)
    await session.commit()

    response.set_cookie("anon_id", make_anon_cookie_val(new_id), max_age=60*60*24*365*2, httponly=True, samesite="lax", secure=False)
    return user
