from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from app.frontend import routes as frontend_routes
from app.api import recipes as recipes_api_mod
from app.api import actions as actions_api_mod
from app.api import search as search_api_mod

app = FastAPI(title="What2Cook", version="0.3.0")

app.include_router(search_api_mod.router)
app.include_router(actions_api_mod.router)
app.include_router(recipes_api_mod.router)

# frontend
app.include_router(frontend_routes.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
