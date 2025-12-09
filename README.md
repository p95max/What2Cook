# What2Cook

[![Python](https://img.shields.io/badge/python-3.14-blue)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Async](https://img.shields.io/badge/async-asyncio-306998?logo=python&logoColor=white)](https://docs.python.org/3/library/asyncio.html)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Container-2496ED?logo=docker&logoColor=white)](https://www.docker.com)


**What2Cook** — lightweight recipe finder: give it the ingredients you have and it will suggest recipes.
Built with **FastAPI**, **async SQLAlchemy**, **Postgres**, **Jinja2 templates** and a small, responsive frontend.

---

## Quick overview

* **API**: FastAPI (OpenAPI docs available at `/docs`).
* **Frontend**: Server-side rendered pages (Jinja2) + small JS for search, likes/bookmarks and copy link.
* **DB**: PostgreSQL (tested with Postgres 17) using asyncpg and SQLAlchemy 2.x (async).
* **Auth model**: anonymous users tracked by a signed cookie (`anon_id`). Likes and bookmarks are stored in the DB but associated with that anonymous user; bookmarks can be fetched and cleared by the same browser cookie.
* **Packaging**: Poetry + pyproject.
* **Containerized**: Dockerfile + `docker-compose.yml` + `docker-compose.override.yml` for local dev (hot reload).

---

## Features

* Search recipes by ingredients (several endpoints: `search`, `search_simple`).
* Mapping user free-text ingredient inputs to canonical DB ingredient names (fuzzy/ILike fallback).
* Bookmark and Like actions for anon users (stored server-side + cookie to identify the user).
* Small responsive UI: index carousel, catalog, search, bookmarks, recipe detail.
* Fixtures loader to populate example recipes & ingredients (fixtures/recipes_fixtures.py).
* Alembic migrations included (`alembic/versions/ca3137948eb4_initial.py`).

---

## Tech stack

* Python 3.14
* FastAPI
* SQLAlchemy (async)
* asyncpg
* PostgreSQL 17
* Alembic
* Jinja2 templates + Bootstrap 5
* Poetry for dependency management
* Docker + docker-compose for local/dev deployment

---

## Getting started (Docker)

**1. Copy `.env.example` to `.env` and update values**

```bash
cp .env.example .env
# Edit .env to set a secure SECRET_KEY and (optionally) SPOONACULAR_API_KEY
```

**2. Build & run**

```bash
docker compose up -d
docker compose exec -e PYTHONPATH=/app web alembic upgrade head
docker compose logs -f web
```

**3. Create / migrate DB (inside container)**

```bash
# open a shell in web container
docker compose exec web alembic upgrade head
```

**4. (Optional) Load fixtures**

```bash
docker compose exec -e PYTHONPATH=/app web python fixtures/recipes_fixtures.py
```

**5. Open**

* Web UI: `http://localhost:8000/`
* API docs (Swagger UI): `http://localhost:8000/docs`

**Dev override**

`docker-compose.override.yml` enables hot reload for the `web` service (uses `uvicorn --reload`).

---

## Running locally (without Docker)

1. Install with Poetry:

```bash
poetry install --no-dev
# or with dev deps
poetry install
```

2. Set `DATABASE_URL` in env (see `.env.example`) and run migrations:

```bash
alembic upgrade head
```

3. Run dev server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Useful commands

From project root (Docker):

```bash
# start
docker compose up --build -d
# show logs
docker compose logs -f web
# stop
docker compose down
# restart web only
docker compose restart web
```

Alembic and DB helpers (examples from NOTES.md):

```bash
docker compose exec web alembic revision --autogenerate -m "init"
docker compose exec web alembic upgrade head
# drop and recreate public schema
docker compose exec db bash -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"'
```

Load fixtures:

```bash
docker compose exec -e PYTHONPATH=/app web python fixtures/recipes_fixtures.py
```

---

## API highlights

* `GET /api/recipes/` — paginated list of recipes (used by frontend list/catalog).
* `GET /api/recipes/{id}` — get single recipe (detailed JSON).
* `GET /api/recipes/{id}/actions` — returns `liked`, `bookmarked`, `likes_count` for current anon user.
* `POST /api/recipes/{id}/like` — toggle like for current anon user.
* `POST /api/recipes/{id}/bookmark` — toggle bookmark.
* `POST /api/recipes/clear` — clear anon data (deletes anon user + actions). Requires `X-Requested-With: XMLHttpRequest` header.
* `GET /api/recipes/ingredients?q=...` — list ingredient names (prefix filter).
* `GET /api/recipes/search_simple?ingredient=egg&ingredient=onion` — search by repeating `ingredient` params (returns simple JSON used by frontend).
* `GET /api/recipes/search?ingredients=egg,onion` — search by comma/newline separated ingredients (used by search page).

All API endpoints expect/return JSON and are implemented with async SQLAlchemy.

---

## Frontend pages

* `/` — landing page with popular recipes carousel
* `/catalog` — paginated catalog
* `/search` — interactive search by ingredients
* `/recipes/{id}` — recipe detail page with like/bookmark/copy link buttons
* `/bookmarks` — list of recipes bookmarked from the current browser cookie

JavaScript modules of interest: `app/static/js/search.js`, `actions.js`, `copy_link.js`, `carousel_swiper.js`.

---

## Data model notes

* `ingredients` table stores canonical ingredient names (with optional `aliases` JSON).
* `recipes` and a `recipe_ingredient` association table connect recipes and ingredients.
* `anon_user` table stores anonymous user rows (identified by a signed cookie using `itsdangerous`).
* `recipe_action` stores likes/bookmarks linked to anon users (unique constraint on anon_id+recipe+action_type).

---

## Testing

Project includes dev/test deps in `pyproject.toml`. Run tests with:

```bash
poetry run pytest
# or inside container if tests included
docker compose exec web pytest
```

---

## Tips & debugging

* If images fail to load locally, check `thumbnail_url`/`image_url` in DB fixtures; remote URLs may be blocked on some networks.
* If you get DB errors during migrations, inspect ALEMBIC config and `DATABASE_URL` (see `alembic/env.py`).
* Use `docker compose exec web ls -la alembic/versions` to inspect migration files inside container.

---

## Contributing

Contributions are welcome — open issues or PRs with small, focused changes. For larger changes, describe the design first.

* Follow project formatting tools (`black`, `ruff`, `isort`).
* Add tests for new logic.

---

## Author

`maxx` — contact: `m.petrykin@gmx.de` (listed in `pyproject.toml`).

---

