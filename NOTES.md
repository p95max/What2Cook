# Docker
docker compose up --build -d
docker compose logs -f web

docker compose down

docker compose restart web

# Migrations
docker compose exec web alembic revision --autogenerate -m "init"
docker compose exec web alembic upgrade head

# Load fixtures to db
docker compose exec -e PYTHONPATH=/app web python scripts/fixtures.py



