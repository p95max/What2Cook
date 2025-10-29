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

# DROP
docker compose exec db bash -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"'

docker compose exec db bash -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT * FROM pg_tables WHERE tablename = '\''alembic_version'\'';"'
docker compose exec db bash -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "DELETE FROM alembic_version;"' || true



# fixtures for db
docker compose exec -e PYTHONPATH=/app web python fixtures/recipes_fixtures.py







