#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "=== Stopping existing containers ==="
docker compose down

echo "=== Starting database ==="
docker compose up -d db

echo "=== Waiting for database to be ready ==="
until docker compose exec -T db pg_isready -U ai_service -d ai_service_db > /dev/null 2>&1; do
    echo "Waiting for PostgreSQL..."
    sleep 1
done

echo "=== Database is ready! ==="
echo ""
echo "Connection string: postgresql://ai_service:ai_service_pass@localhost:5436/ai_service_db"
echo ""
echo "To run migrations: alembic upgrade head"
echo "To run tests: pytest -v"
echo "To stop: docker compose down"
