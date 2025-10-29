"""
Centralized Jinja2Templates instance and configuration.

Use this module to import `templates` everywhere (avoid multiple
Jinja2Templates creations & circular imports).
"""
from pathlib import Path
from fastapi.templating import Jinja2Templates
from jinja2 import FileSystemLoader

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

try:
    templates.env.auto_reload = True
    templates.env.loader = FileSystemLoader(str(TEMPLATES_DIR))
    templates.env.cache = {}
except Exception:
    pass
