#!/bin/bash
set -e

echo "========================================="
echo "QueryCraft Django Application Startup"
echo "========================================="

# Wait for database to be ready (if DATABASE_URL is set)
if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for database to be ready..."

    # Extract host and port from DATABASE_URL
    # Format: postgresql://user:pass@host:port/db
    DB_HOST=$(echo $DATABASE_URL | sed -n 's|.*@\([^:]*\):[0-9]*/.*|\1|p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's|.*@[^:]*:\([0-9]*\)/.*|\1|p')

    if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
        MAX_RETRIES=30
        RETRY_COUNT=0

        until curl -s "http://$DB_HOST:$DB_PORT" > /dev/null 2>&1 || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
            RETRY_COUNT=$((RETRY_COUNT+1))
            echo "Waiting for database... ($RETRY_COUNT/$MAX_RETRIES)"
            sleep 2
        done

        if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
            echo "Warning: Could not connect to database, but continuing anyway..."
        else
            echo "Database is ready!"
        fi
    fi
fi

# Run database migrations
echo ""
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files (skip in dev mode if SKIP_COLLECTSTATIC is set)
if [ -z "$SKIP_COLLECTSTATIC" ]; then
    echo ""
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
else
    echo ""
    echo "Skipping collectstatic (SKIP_COLLECTSTATIC is set)"
fi

# Seed database if SEED_DB environment variable is set
if [ "$SEED_DB" = "true" ]; then
    echo ""
    echo "Seeding database with sample data..."
    python manage.py seed_db || echo "Seed command failed or data already exists"
fi

echo ""
echo "========================================="
echo "Starting application..."
echo "========================================="
echo ""

# Execute the main command
exec "$@"
