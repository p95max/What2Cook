from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from app.api import recipes as recipes_api_mod
from app.frontend import routes as frontend_routes

app = FastAPI(title="What2Cook", version="0.3.0")
app.include_router(recipes_api_mod.router, prefix="/api/recipes", tags=["api", "recipes"])
app.include_router(frontend_routes.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
