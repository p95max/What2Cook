from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.recipes import router as api_router
from app.frontend.routes import router as frontend_router

app = FastAPI(title="What2Cook", version="0.3.0")
app.include_router(api_router, prefix="/api")
app.include_router(frontend_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
