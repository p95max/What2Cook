"""
Main FastAPI application for What2Cook.
"""
import os
from fastapi import FastAPI
from app.api import router as api_router
from app.db import init_db

app = FastAPI(title="What2Cook", version="0.1.0")
app.include_router(api_router, prefix="/api")

@app.on_event("startup")
async def on_startup() -> None:
    if os.getenv("AUTO_INIT_DB", "true").lower() in ("1", "true", "yes"):
        await init_db()
