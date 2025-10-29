# Docker
docker compose up --build -d
docker compose logs -f web

docker compose down

docker compose restart web

# Migrations
docker compose exec web alembic revision --autogenerate -m "init"
docker compose exec web alembic upgrade head

docker compose exec web alembic heads
docker compose exec -e PYTHONPATH=/app web alembic current
docker compose exec web ls -la alembic/versions

# fixtures for db
docker compose exec -e PYTHONPATH=/app web python fixtures/recipes_fixtures.py







