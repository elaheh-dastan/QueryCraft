# QueryCraft 🔍

A Django web application that converts natural language questions to SQL queries using an AI Agent
and extracts results from the database.

## Features

- ✨ Convert natural language questions to SQL using local LLM (Ollama)
- 🗄️ PostgreSQL database backend
- 🐳 Fully Dockerized with multiple deployment profiles (dev, staging, production)
- 🎨 Beautiful and modern UI
- 🔒 Secure and reliable with SQL validation
- 🤖 Local LLM inference with sqlcoder-7b-2 model (Q4_K_M quantization)
- 🔄 LangGraph workflow for SQL generation, validation, and execution
- 🛠️ Task automation with Justfile

## Architecture

The project uses Docker Compose with deployment profiles:

**Services:**
1. **db** - PostgreSQL 18 database
2. **ollama** - Local LLM service running `sqlcoder-7b-2:local` model
3. **web** - Django application (staging profile)
4. **web-prod** - Django application (production profile)

**Deployment Modes:**
- **Local Development**: Django runs locally, services in Docker (recommended for development)
- **Staging**: All services in Docker with `--profile stage`
- **Production**: All services in Docker with `--profile prod`

## Quick Start (Recommended)

### Prerequisites

- Docker and Docker Compose
- Just (optional but recommended): `cargo install just` or `brew install just`
- At least 8GB RAM (for Ollama model)
- Python 3.11+ (for local development)

### Option 1: Staging Deployment (Full Docker)

**Using Justfile (Recommended):**

```bash
# Full staging deployment (build + start + migrate)
just stage-deploy

# Create sample data
just stage-exec "python manage.py create_sample_data"

# Access application at http://localhost:8000
```

**Using Docker Compose directly:**

```bash
# Start staging environment
docker compose --profile stage up -d

# Wait for services, then run migrations
docker compose --profile stage exec web python manage.py migrate

# Create sample data
docker compose --profile stage exec web python manage.py create_sample_data

# Access application at http://localhost:8000
```

### Option 2: Local Development (Recommended for Development)

Run Django locally with database and Ollama in Docker for better IDE integration:

**Using Justfile (Recommended):**

```bash
# One-time setup: start services, migrate, create sample data
just dev-setup

# Run Django locally
just runserver

# Access application at http://localhost:8000
```

**Manual steps:**

```bash
# Install dependencies
uv sync

# Start only database and Ollama services
docker compose up -d db ollama

# Run migrations
uv run python manage.py migrate

# Create sample data
uv run python manage.py create_sample_data

# Run development server
uv run python manage.py runserver
```

### Model Setup

On first run, the Ollama service will automatically:
- Download the custom GGUF model file from HuggingFace (~4.5GB)
- Import the model as `sqlcoder-7b-2:local`

This may take 10-15 minutes depending on your internet connection.
The model is cached in the `models/` directory and `ollama_data` volume.

Monitor setup progress:
```bash
docker compose logs -f ollama
```

### Creating Sample Data

The `create_sample_data` command creates a small test dataset:
- 20 customers (30% from last month, 20% from this month, 50% older)
- 15 products across various categories
- 50 orders linking customers and products

**Customize the data:**
```bash
# Staging
just stage-exec "python manage.py create_sample_data --customers 50 --products 30 --orders 100"

# Local development
uv run python manage.py create_sample_data --customers 50 --products 30 --orders 100
```

## Justfile Commands Reference

The project includes a comprehensive Justfile for task automation. Run `just` or `just --list` to see all commands.

### Common Commands

```bash
# Local Development
just dev-setup          # One-time setup: start services, migrate, seed
just dev-services       # Start only DB and Ollama
just runserver          # Run Django locally
just dev-logs           # View service logs

# Staging Deployment
just stage-deploy       # Full deploy: build + up + migrate
just stage-up           # Start staging
just stage-logs         # View logs
just stage-down         # Stop staging

# Production Deployment
just prod-validate      # Validate .env for production
just prod-deploy        # Full deploy with validation
just prod-up            # Start production
just prod-down          # Stop production

# Database Management
just db-backup          # Backup database
just db-restore         # Restore database
just db-shell           # PostgreSQL CLI

# Code Quality
just lint               # Run ruff and mypy
just sync               # Sync dependencies
```

### Docker Compose Commands (Alternative)

If you prefer not to use Just, you can use Docker Compose directly:

```bash
# Staging
docker compose --profile stage up -d
docker compose --profile stage logs -f
docker compose --profile stage exec web python manage.py migrate
docker compose --profile stage exec web python manage.py createsuperuser
docker compose --profile stage down

# Production
docker compose --profile prod up -d
docker compose --profile prod logs -f
docker compose --profile prod exec web-prod python manage.py migrate
docker compose --profile prod down

# Services only (for local development)
docker compose up -d db ollama
docker compose logs -f ollama
docker compose down

# Check Ollama model
docker compose exec ollama ollama list
docker compose exec ollama ollama show sqlcoder-7b-2:local
```

## Production Deployment

### Prerequisites

- Docker and Docker Compose
- Domain name (for production)
- Valid SSL certificate (recommended)
- At least 8GB RAM

### Setup Steps

1. **Create production environment file**
   ```bash
   cp .env.prod.example .env
   ```

2. **Configure production settings in `.env`**
   - Set a strong `SECRET_KEY` (generate with: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`)
   - Set `DEBUG=0`
   - Configure `ALLOWED_HOSTS` with your domain(s)
   - Set a strong `POSTGRES_PASSWORD`

3. **Validate and deploy**
   ```bash
   # Validate configuration
   just prod-validate

   # Full production deployment
   just prod-deploy
   ```

4. **Create superuser**
   ```bash
   just prod-exec "python manage.py createsuperuser"
   ```

## Local Development (Without Docker)

### Prerequisites

- Python 3.11+
- uv (install with pipx: `pipx install uv`)
- PostgreSQL 18+ (must be running)
- Ollama installed locally

### Setup Steps

1. **Install `uv`**

   ```bash
   pipx install uv
   ```

2. **Install dependencies**

   ```bash
   uv pip install -e .
   ```

3. **Install and setup Ollama locally**

   ```bash
   # Install Ollama (see https://ollama.ai)

   # Download the custom GGUF model
   mkdir -p models
   curl -L -o models/sqlcoder-7b-2.Q4_K_M.gguf \
     https://huggingface.co/MaziyarPanahi/sqlcoder-7b-2-GGUF/resolve/main/sqlcoder-7b-2.Q4_K_M.gguf

   # Create model using the provided Modelfile
   ollama create sqlcoder-7b-2:local -f Modelfile
   ```

4. **Configure database connection**

   ```bash
   # Set PostgreSQL connection (optional, auto-detected if running locally)
   export POSTGRES_HOST=localhost
   export POSTGRES_PORT=5432
   export POSTGRES_USER=querycraft
   export POSTGRES_PASSWORD=querycraft_password
   export POSTGRES_DB=querycraft
   ```

5. **Run migrations**

   ```bash
   uv run python manage.py migrate
   ```

6. **Create sample data**

   ```bash
   uv run python manage.py create_sample_data
   ```

   Customize if needed:
   ```bash
   uv run python manage.py create_sample_data --customers 50 --products 30 --orders 100
   ```

7. **Create superuser (optional)**

   ```bash
   uv run python manage.py createsuperuser
   ```

8. **Run development server**

   ```bash
   uv run python manage.py runserver
   ```

9. **Access the application**
   ```
   http://127.0.0.1:8000
   ```

## Using the Application

### Web Interface

1. Open the main page at `http://localhost:8000`
2. Write a natural language question, for example:
   - "How many customers registered last month?"
   - "Show all products in the Electronics category"
   - "What is the total number of orders?"
3. Click the "Convert to SQL and Execute" button
4. View the generated SQL query and results

### API Client Interface

1. Open the API client page at `http://localhost:8000/api-client/`
2. Enter your question in the text area
3. Click "Send Query" to see the API response
4. View the full JSON response including SQL query and results

### API Endpoint

The application provides a REST API endpoint for programmatic access:

**Endpoint:** `POST /query/api/`

**Request:**

```json
{
  "question": "How many customers registered last month?"
}
```

**Response (Success):**

```json
{
  "success": true,
  "question": "How many customers registered last month?",
  "sql_query": "SELECT COUNT(*) FROM querycraft_customer WHERE registration_date >= date('now', '-1 month')",
  "method": "ollama",
  "results": [
    {
      "COUNT(*)": 45
    }
  ],
  "row_count": 1,
  "columns": ["COUNT(*)"],
  "error": null
}
```

**Response (Error):**

```json
{
  "success": false,
  "question": "Invalid question",
  "sql_query": null,
  "method": null,
  "error": "SQL query validation failed",
  "results": [],
  "row_count": 0,
  "columns": []
}
```

**Example using curl:**

```bash
curl -X POST http://localhost:8000/query/api/ \
  -H "Content-Type: application/json" \
  -d '{"question": "How many customers registered last month?"}'
```

**Example using Python:**

```python
import requests

response = requests.post(
    'http://localhost:8000/query/api/',
    json={'question': 'How many customers registered last month?'}
)
data = response.json()
print(data)
```

## Project Structure

```
QueryCraft/
├── querycraft_project/         # Main Django project settings
│   ├── settings.py             # Auto-configured for dev/Docker
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── querycraft/                 # Main application
│   ├── models.py               # Database models (Customer, Product, Order)
│   ├── views.py                # Application views
│   ├── services.py             # AI Agent service (LangGraph + Ollama)
│   ├── urls.py                 # URL routing
│   ├── admin.py                # Admin configuration
│   ├── templates/              # HTML templates
│   │   ├── query_form.html
│   │   └── api_client.html
│   └── management/commands/    # Custom Django commands
│       └── create_sample_data.py
├── models/                     # GGUF model storage (created on first run)
├── docker-compose.yml          # Docker Compose with profiles (stage/prod)
├── Dockerfile                  # Multi-stage build for web service
├── Dockerfile.ollama           # Ollama service with model setup
├── entrypoint.sh               # Web service entrypoint
├── entrypoint.ollama.sh        # Ollama service entrypoint
├── Modelfile                   # Ollama model configuration
├── init_ollama.sh              # Script to setup custom model
├── justfile                    # Task automation (recommended)
├── pyproject.toml              # Python dependencies (Django 5.2+, Python 3.11+)
├── .env.example                # Environment variables template
├── .env.prod.example           # Production environment template
└── manage.py                   # Django management script
```

## Configuration

### Environment Variables

Key environment variables (see `.env.example` for full list):

- `DEBUG`: Debug mode (default: 1 for dev, must be 0 for production)
- `SECRET_KEY`: Django secret key (must be set for production)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `POSTGRES_DB`: Database name (default: querycraft)
- `POSTGRES_USER`: Database user (default: querycraft)
- `POSTGRES_PASSWORD`: Database password (default: querycraft_password, change for production)
- `POSTGRES_HOST`: Database host (auto-detected: 'localhost' or 'db')
- `OLLAMA_BASE_URL`: Ollama service URL (auto-detected: 'http://localhost:11434' or 'http://ollama:11434')
- `OLLAMA_MODEL_NAME`: Model name (default: sqlcoder-7b-2:local)

**Auto-detection:**
- Settings automatically detect if running in Docker or locally
- Database and Ollama URLs are configured appropriately
- No `.env` file needed for basic local development

### Database

The project uses **PostgreSQL 18** exclusively:
- In Docker: PostgreSQL runs in a container
- Local development: Connect to PostgreSQL in Docker or a local instance
- **SQLite is not supported** (PostgreSQL-specific features are used)

### Ollama Model

The application uses `sqlcoder-7b-2:local` (Q4_K_M quantization):

- **Source**: HuggingFace (MaziyarPanahi/sqlcoder-7b-2-GGUF)
- **File**: sqlcoder-7b-2.Q4_K_M.gguf
- **Format**: GGUF quantized model
- **Optimized for**: SQL generation from natural language
- **Quantization**: Q4_K_M for efficient inference (~4.5GB)
- **Setup**: Automatically downloaded and imported on first run
- **Storage**: `models/` directory + Docker volume `ollama_data`
- **Privacy**: Runs entirely locally, no API keys needed

**Model Setup Process:**
1. `entrypoint.ollama.sh` starts Ollama service
2. `init_ollama.sh` checks if model exists
3. If needed, imports model from GGUF file using Modelfile
4. Model is registered as `sqlcoder-7b-2:local` in Ollama

## AI Agent & LangGraph Workflow

The application uses a LangGraph workflow for processing natural language questions:

1. **Node 1: SQL Generator** - Uses Ollama with sqlcoder-7b-2 model to generate SQL from natural language
2. **Node 2: SQL Validator** - Validates the generated SQL for:
   - Syntax correctness
   - Safety (only SELECT queries allowed)
   - Table name validation
   - Dangerous operation detection
3. **Node 3: Execute SQL** - Executes validated SQL and returns results

The workflow ensures that only safe, validated SQL queries are executed against the database.

## Database Schema

The application uses three main tables:

1. **customers** - Customer information

   - id, name, email, registration_date

2. **products** - Product catalog

   - id, name, category, price

3. **orders** - Customer orders
   - id, customer_id, product_id, order_date, quantity, status

## Example Questions

- "How many customers registered last month?"
- "Show all products in the Electronics category"
- "What is the total number of orders?"
- "List all orders for customer with id 5"
- "Show products with price greater than 100"
- "تمام مشتریانی که در ۱۰ روز اخیر در سایت ما ثبتنام داشتند." (All customers who registered in the last 10 days - Persian)

## Development

### Local Development Workflow

**Recommended approach using Justfile:**

```bash
# Start services (DB + Ollama)
just dev-services

# Run Django locally with hot-reload
just runserver

# Run linting and type checking
just lint

# Create migrations
just makemigrations

# Apply migrations
just migrate
```

**Project customization:**

1. Add new models in `querycraft/models.py`
2. Modify SQL generation prompts in `querycraft/services.py`
3. Customize the UI in `querycraft/templates/querycraft/`
4. Add management commands in `querycraft/management/commands/`

### Code Quality Tools

The project uses **ruff** and **mypy** for code quality and type checking.

**Install development dependencies:**

```bash
uv sync
```

**Run linting and type checking:**

```bash
# Using Justfile (recommended)
just lint

# Or manually
uv run ruff check --fix .
uv run ruff format .
uv run mypy .
```

**Configuration:**
- Ruff: Configured in `pyproject.toml` (line length: 100, Python 3.11+)
- Mypy: Configured in `pyproject.toml` with django-stubs plugin

### Sample Data Management

The `create_sample_data` management command creates test data:

- **Maintains Referential Integrity**: All foreign keys reference valid records
- **Time-distributed Data**: Customers distributed across time periods (last month, this month, older)
- **Configurable**: Customize the number of records via command-line arguments

**Usage:**

```bash
# Default: 20 customers, 15 products, 50 orders
python manage.py create_sample_data

# Custom amounts
python manage.py create_sample_data --customers 50 --products 30 --orders 100
```

**Note:** The command clears existing data before creating new records.

## Troubleshooting

### Ollama Model Issues

**Check if model is loaded:**

```bash
# Using Justfile
just ollama-list

# Or directly
docker compose exec ollama ollama list
```

You should see `sqlcoder-7b-2:local` in the list.

**If model is missing:**

1. Check Ollama logs:
   ```bash
   docker compose logs -f ollama
   ```

2. Manually run setup script:
   ```bash
   docker compose exec ollama /app/init_ollama.sh
   ```

3. Verify model file exists:
   ```bash
   ls -lh models/sqlcoder-7b-2.Q4_K_M.gguf
   ```

4. Manually import model:
   ```bash
   just ollama-create
   # Or: docker compose exec ollama ollama create sqlcoder-7b-2:local -f /app/Modelfile
   ```

### Service Issues

**Ollama not responding:**

```bash
# Check service status
just health-check

# Restart Ollama
docker compose restart ollama

# View logs
docker compose logs -f ollama
```

**Database connection issues:**

```bash
# Check database is ready
docker compose exec db pg_isready -U querycraft

# Access database shell
just db-shell

# Restart database
docker compose restart db
```

**Web service issues:**

```bash
# Staging
docker compose --profile stage logs -f web
docker compose --profile stage restart web

# Production
docker compose --profile prod logs -f web-prod
docker compose --profile prod restart web-prod
```

### Performance Issues

**Out of memory errors:**

The sqlcoder model requires ~4-6GB RAM:

- Ensure Docker has 8GB+ memory allocated
- Check: Docker Desktop → Settings → Resources
- Close other memory-intensive applications
- Monitor usage: `docker stats`

**Model download timeout:**

If download fails or times out:

1. Check internet connection
2. Manually download model:
   ```bash
   cd models
   curl -L -O https://huggingface.co/MaziyarPanahi/sqlcoder-7b-2-GGUF/resolve/main/sqlcoder-7b-2.Q4_K_M.gguf
   ```
3. Restart Ollama: `docker compose restart ollama`

### Docker Compose Profile Issues

**"service web is not running" error:**

The `web` service requires the `stage` profile:

```bash
# Wrong
docker compose up

# Correct
docker compose --profile stage up
# Or: just stage-up
```

**Profile reference:**
- No profile: Only `db` and `ollama` start
- `--profile stage`: Starts `web` (staging)
- `--profile prod`: Starts `web-prod` (production)

## License

This project is free for educational and commercial use.

## Support

For issues and questions, please create an issue on the repository.
