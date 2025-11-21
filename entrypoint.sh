#!/bin/bash
set -e

echo "========================================="
echo "QueryCraft Django Application Startup"
echo "========================================="

echo "Waiting for database to be ready..."

MAX_RETRIES=30
RETRY_COUNT=0

until uv run manage.py inspectdb >/dev/null 2>&1 || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
	RETRY_COUNT=$((RETRY_COUNT + 1))
	echo "Waiting for database... ($RETRY_COUNT/$MAX_RETRIES)"
	sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
	echo "Warning: Could not connect to database, but continuing anyway..."
else
	echo "Database is ready!"
fi

# Run database migrations
echo ""
echo "Running database migrations..."
uv run manage.py migrate --noinput

# Seed database if SEED_DB environment variable is set
if [ "$SEED_DB" = "true" ]; then
	echo ""
	echo "Seeding database with sample data..."
	uv run manage.py seed_db || echo "Seed command failed or data already exists"
fi

echo ""
echo "========================================="
echo "Starting application..."
echo "========================================="
echo ""

# Execute the main command
exec "$@"
