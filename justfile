@default:
    @just --list

# ============================================
# Python Development
# ============================================

# Sync dependencies from pyproject.toml
sync:
    uv sync

# Upgrade all packages to latest versions
upgrade:
    uv lock --upgrade
    uv sync

# Run linting and type checking
lint:
    uv run ruff check --fix .
    uv run ruff format .
    uv run mypy .

# Run Django development server locally
runserver:
    uv run python manage.py runserver

# Create Django migrations
makemigrations:
    uv run python manage.py makemigrations

# Apply Django migrations
migrate:
    uv run python manage.py migrate

# Create superuser for Django admin
createsuperuser:
    uv run python manage.py createsuperuser

# Create sample data for testing
seed:
    uv run python manage.py create_sample_data

# Open Django shell
shell:
    uv run python manage.py shell

# ============================================
# Model Management
# ============================================

[working-directory("models")]
download-model:
    wget 'https://huggingface.co/MaziyarPanahi/sqlcoder-7b-2-GGUF/resolve/main/sqlcoder-7b-2.Q4_K_M.gguf'

# ============================================
# Docker Compose - Development (Hybrid Mode)
# ============================================
# Use these when running Django locally with Docker services

# Build development images
dev-build:
    docker compose build

# Start only database and Ollama services (for local Django development)
dev-services:
    docker compose up -d db ollama

# Stop development services
dev-services-down:
    docker compose down

# View logs from development services
dev-logs service="":
    #!/usr/bin/env bash
    if [ -z "{{ service }}" ]; then
        docker compose logs -f db ollama
    else
        docker compose logs -f {{ service }}
    fi

# Restart development services
dev-services-restart:
    docker compose restart db ollama

# Check status of development services
dev-status:
    docker compose ps db ollama

# Full development setup (start services + migrate + seed)
dev-setup:
    @echo "Starting Docker services..."
    docker compose up -d db ollama
    @echo "Waiting for services to be ready..."
    sleep 10
    @echo "Running migrations..."
    uv run python manage.py migrate
    @echo "Creating sample data..."
    uv run python manage.py create_sample_data
    @echo ""
    @echo "Development setup complete!"
    @echo "Run 'just runserver' to start Django development server"

# ============================================
# Docker Compose - Staging Environment
# ============================================

# Build staging images
stage-build:
    docker compose --profile stage build

# Start staging environment
stage-up:
    docker compose --profile stage up -d

# Start staging with logs
stage-up-logs:
    docker compose --profile stage up

# Stop staging environment
stage-down:
    docker compose --profile stage down

# Restart staging environment
stage-restart:
    docker compose --profile stage restart

# View staging logs
stage-logs service="":
    #!/usr/bin/env bash
    if [ -z "{{ service }}" ]; then
        docker compose --profile stage logs -f
    else
        docker compose --profile stage logs -f {{ service }}
    fi

# Check staging status
stage-status:
    docker compose --profile stage ps

# Execute command in staging web container
stage-exec cmd:
    docker compose --profile stage exec web {{ cmd }}

# Run migrations in staging
stage-migrate:
    docker compose --profile stage exec web python manage.py migrate

# Create superuser in staging
stage-superuser:
    docker compose --profile stage exec web python manage.py createsuperuser

# Full staging deployment (build + up + migrate)
stage-deploy:
    @echo "Building staging images..."
    docker compose --profile stage build
    @echo "Starting staging containers..."
    docker compose --profile stage up -d
    @echo "Waiting for services to be ready..."
    sleep 15
    @echo "Running migrations..."
    docker compose --profile stage exec web python manage.py migrate
    @echo ""
    @echo "Staging deployment complete!"
    @echo "Access at: http://localhost:8000"

# ============================================
# Docker Compose - Production Environment
# ============================================

# Build production images
prod-build:
    docker compose --profile prod build

# Start production environment
prod-up:
    docker compose --profile prod up -d

# Start production with logs
prod-up-logs:
    docker compose --profile prod up

# Stop production environment
prod-down:
    docker compose --profile prod down

# Restart production environment
prod-restart:
    docker compose --profile prod restart

# View production logs
prod-logs service="":
    #!/usr/bin/env bash
    if [ -z "{{ service }}" ]; then
        docker compose --profile prod logs -f
    else
        docker compose --profile prod logs -f {{ service }}
    fi

# Check production status
prod-status:
    docker compose --profile prod ps

# Execute command in production web container
prod-exec cmd:
    docker compose --profile prod exec web-prod {{ cmd }}

# Run migrations in production
prod-migrate:
    docker compose --profile prod exec web-prod python manage.py migrate

# Create superuser in production
prod-superuser:
    docker compose --profile prod exec web-prod python manage.py createsuperuser

# Collect static files in production
prod-collectstatic:
    docker compose --profile prod exec web-prod python manage.py collectstatic --noinput

# Validate production environment variables before deployment
prod-validate:
    #!/usr/bin/env bash
    set -e
    echo "Validating production environment..."
    echo ""

    # Check if .env file exists
    if [ ! -f .env ]; then
        echo "✗ ERROR: .env file not found"
        echo "  Run: cp .env.prod.example .env"
        exit 1
    fi

    # Source .env file
    set -a
    source .env
    set +a

    # Check SECRET_KEY
    if [ -z "$SECRET_KEY" ] || [[ "$SECRET_KEY" == *"CHANGE-THIS"* ]] || [[ "$SECRET_KEY" == *"django-insecure"* ]]; then
        echo "✗ ERROR: SECRET_KEY is not set or uses default value"
        echo "  Generate with: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
        exit 1
    fi
    echo "✓ SECRET_KEY is set"

    # Check DEBUG
    if [ "$DEBUG" = "1" ]; then
        echo "⚠ WARNING: DEBUG=1 in production is not recommended"
    else
        echo "✓ DEBUG is disabled"
    fi

    # Check ALLOWED_HOSTS
    if [ -z "$ALLOWED_HOSTS" ] || [ "$ALLOWED_HOSTS" = "localhost,127.0.0.1" ]; then
        echo "✗ ERROR: ALLOWED_HOSTS must be set to your domain(s)"
        echo "  Example: ALLOWED_HOSTS=example.com,www.example.com"
        exit 1
    fi
    echo "✓ ALLOWED_HOSTS is configured: $ALLOWED_HOSTS"

    # Check POSTGRES_PASSWORD
    if [ -z "$POSTGRES_PASSWORD" ] || [[ "$POSTGRES_PASSWORD" == *"CHANGE-THIS"* ]] || [ "$POSTGRES_PASSWORD" = "querycraft_password" ]; then
        echo "✗ ERROR: POSTGRES_PASSWORD uses default or placeholder value"
        echo "  Set a strong password in .env"
        exit 1
    fi
    echo "✓ POSTGRES_PASSWORD is set"

    echo ""
    echo "✓ Production environment validation passed!"
    echo ""

# Full production deployment with validation (build + up + migrate + collectstatic)
prod-deploy:
    @echo "Step 1: Validating production environment..."
    @just prod-validate
    @echo ""
    @echo "Step 2: Building production images..."
    docker compose --profile prod build
    @echo ""
    @echo "Step 3: Starting production containers..."
    docker compose --profile prod up -d
    @echo ""
    @echo "Step 4: Waiting for services to be ready..."
    sleep 15
    @echo ""
    @echo "Step 5: Running migrations..."
    docker compose --profile prod exec web-prod python manage.py migrate
    @echo ""
    @echo "Step 6: Collecting static files..."
    docker compose --profile prod exec web-prod python manage.py collectstatic --noinput
    @echo ""
    @echo "========================================="
    @echo "✓ Production deployment complete!"
    @echo "========================================="
    @echo "Access at: http://localhost:8000"
    @echo ""

# ============================================
# Docker Compose - General Management
# ============================================

# Stop all Docker Compose services (all profiles)
docker-down-all:
    docker compose --profile stage --profile prod down

# Remove all containers, networks, and volumes
docker-clean:
    docker compose --profile stage --profile prod down -v
    docker system prune -f

# View all running containers
docker-ps:
    docker compose ps -a

# Show Docker disk usage
docker-usage:
    docker system df

# Pull latest base images
docker-pull:
    docker compose pull

# Rebuild all images from scratch (no cache)
docker-rebuild profile="stage":
    docker compose --profile {{ profile }} build --no-cache

# View resource usage of containers
docker-stats:
    docker stats

# ============================================
# Database Management
# ============================================

# Backup database to file
db-backup file="backup.sql":
    docker compose exec -T db pg_dump -U querycraft querycraft > {{ file }}
    @echo "Database backed up to {{ file }}"

# Restore database from file
db-restore file="backup.sql":
    docker compose exec -T db psql -U querycraft querycraft < {{ file }}
    @echo "Database restored from {{ file }}"

# Access PostgreSQL CLI
db-shell:
    docker compose exec db psql -U querycraft querycraft

# Reset database (WARNING: deletes all data)
db-reset:
    @echo "WARNING: This will delete all data!"
    @echo "Press Ctrl+C to cancel, or Enter to continue..."
    @read
    docker compose down -v
    docker compose up -d db
    sleep 5
    uv run python manage.py migrate

# ============================================
# Ollama Management
# ============================================

# List Ollama models
ollama-list:
    docker compose exec ollama ollama list

# Pull a model in Ollama
ollama-pull model="sqlcoder-7b-2:local":
    docker compose exec ollama ollama pull {{ model }}

# Create sqlcoder model from Modelfile
ollama-create:
    docker compose exec ollama ollama create sqlcoder-7b-2:local -f /app/Modelfile

# Test Ollama API
ollama-test:
    curl http://localhost:11434/api/tags | jq

# ============================================
# Testing & CI/CD
# ============================================

# Run tests (when implemented)
test:
    uv run pytest

# Run tests with coverage
test-coverage:
    uv run pytest --cov=querycraft --cov-report=html

# Check if Docker Compose configuration is valid
docker-validate:
    docker compose --profile stage config > /dev/null
    docker compose --profile prod config > /dev/null
    @echo "✓ Docker Compose configuration is valid"

# Health check for all services
health-check profile="stage":
    @echo "Checking health of {{ profile }} services..."
    docker compose --profile {{ profile }} ps
    @echo ""
    curl -f http://localhost:8000/ || echo "✗ Web service not responding"
    curl -f http://localhost:11434/api/tags || echo "✗ Ollama service not responding"
    docker compose --profile {{ profile }} exec db pg_isready -U querycraft || echo "✗ Database not ready"

# ============================================
# Quick Reference
# ============================================

# Show help with examples
help:
    @echo "QueryCraft Just Commands"
    @echo "======================="
    @echo ""
    @echo "Development (Local Django + Docker Services):"
    @echo "  just dev-setup          # One-time setup: start services, migrate, seed"
    @echo "  just dev-services       # Start only DB and Ollama"
    @echo "  just runserver          # Run Django locally"
    @echo "  just dev-logs           # View service logs"
    @echo ""
    @echo "Staging Deployment (All in Docker):"
    @echo "  just stage-deploy       # Full deploy: build + up + migrate"
    @echo "  just stage-up           # Start staging"
    @echo "  just stage-logs         # View logs"
    @echo "  just stage-down         # Stop staging"
    @echo ""
    @echo "Production Deployment (All in Docker):"
    @echo "  just prod-validate      # Validate .env for production"
    @echo "  just prod-deploy        # Full deploy: validate + build + up + migrate + static"
    @echo "  just prod-up            # Start production"
    @echo "  just prod-logs          # View logs"
    @echo "  just prod-down          # Stop production"
    @echo ""
    @echo "Database:"
    @echo "  just db-backup          # Backup database"
    @echo "  just db-restore         # Restore database"
    @echo "  just db-shell           # PostgreSQL CLI"
    @echo ""
    @echo "Ollama:"
    @echo "  just ollama-list        # List models"
    @echo "  just ollama-create      # Create sqlcoder model"
    @echo ""
    @echo "Maintenance:"
    @echo "  just docker-clean       # Remove all containers and volumes"
    @echo "  just health-check       # Check service health"
    @echo ""
    @echo "Run 'just' to see all available commands"
