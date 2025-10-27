"""
Async SQLAlchemy engine and session factory for the What2Cook project.
"""
import os
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Copy .env.example to .env and set DATABASE_URL or export it in CI.")


_engine = create_async_engine(
    DATABASE_URL,
    future=True,
    echo=(os.getenv("SQL_ECHO", "false").lower() in ("1", "true", "yes")),
)

AsyncSessionLocal = async_sessionmaker(bind=_engine, expire_on_commit=False)
Base = declarative_base()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
