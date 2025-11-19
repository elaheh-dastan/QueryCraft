# QueryCraft 🔍

A Django web application that converts natural language questions to SQL queries using an AI Agent and extracts results from the database.

## Features

- ✨ Convert natural language questions to SQL using local LLM (Ollama)
- 🗄️ Support for SQLite and PostgreSQL
- 🐳 Fully Dockerized with 3 services (web, db, ollama)
- 🎨 Beautiful and modern UI
- 🔒 Secure and reliable
- 🤖 Local LLM inference with sqlcoder-7b-2 model

## Architecture

The project consists of 3 main Docker services:

1. **web** - Django application
2. **db** - PostgreSQL database
3. **ollama** - Local LLM service running sqlcoder-7b-2:Q4_K_M model

## Setup with Docker (Recommended)

### Prerequisites

- Docker
- Docker Compose
- At least 8GB RAM (for Ollama model)

### Setup Steps

1. **Clone or download the project**

2. **Create `.env` file (optional)**
   ```bash
   cp .env.example .env
   ```
   
   Edit the `.env` file if needed (most settings have defaults)

3. **Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```
   
   **Note:** On first run, Ollama will download the sqlcoder-7b-2:Q4_K_M model (~4.5GB). This may take several minutes depending on your internet connection.

4. **Initialize Ollama model (first time only)**
   
   After the containers are up, pull the model:
   ```bash
   docker-compose exec ollama ollama pull sqlcoder-7b-2:Q4_K_M
   ```
   
   This only needs to be done once. The model will be cached in the `ollama_data` volume.

5. **Access the application**
   - Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

6. **Create Django superuser (for Admin access)**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

7. **Create sample data (optional)**
   ```bash
   docker-compose exec web python manage.py create_sample_data
   ```
   This command creates 20 sample customers, 15 products, and 50 orders.

### Useful Docker Commands

```bash
# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f ollama
docker-compose logs -f web

# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes database and models)
docker-compose down -v

# Run Django commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py shell

# Check if Ollama model is loaded
docker-compose exec ollama ollama list

# Pull/update Ollama model
docker-compose exec ollama ollama pull sqlcoder-7b-2:Q4_K_M
```

## Setup without Docker (Local Development)

### Prerequisites

- Python 3.8+
- uv (install with pipx)
- PostgreSQL (optional, SQLite works too)
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
   # Then pull the model:
   ollama pull sqlcoder-7b-2:Q4_K_M
   ```

4. **Set environment variables**
   ```bash
   export OLLAMA_BASE_URL=http://localhost:11434
   ```

5. **Run migrations**
   ```bash
   uv run python manage.py migrate
   ```

6. **Create superuser (optional)**
   ```bash
   uv run python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   uv run python manage.py runserver
   ```

8. **Create sample data (optional)**
   ```bash
   uv run python manage.py create_sample_data
   ```
   This creates sample customers, products, and orders.

9. **Access the application**
   ```
   http://127.0.0.1:8000
   ```

## Using the Application

1. Open the main page
2. Write a natural language question, for example:
   - "How many new users registered last month?"
   - "Show all users"
   - "What is the total number of orders?"
3. Click the "Convert to SQL and Execute" button
4. View the generated SQL query and results

## Project Structure

```
QueryCraft/
├── querycraft_project/     # Main Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── querycraft/             # Main application
│   ├── models.py          # Database models (Customer, Product, Order)
│   ├── views.py           # Application views
│   ├── services.py        # AI Agent service (Ollama integration)
│   ├── urls.py            # URL routing
│   ├── admin.py           # Admin settings
│   └── templates/         # HTML templates
├── docker-compose.yml     # Docker Compose configuration (3 services)
├── Dockerfile             # Docker image for web service
├── pyproject.toml         # Project dependencies
└── manage.py              # Django management script
```

## Configuration

### Environment Variables

- `DEBUG`: Debug mode (default: 1)
- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: Database URL (for PostgreSQL)
- `OLLAMA_BASE_URL`: Ollama service URL (default: http://ollama:11434)
- `ALLOWED_HOSTS`: Allowed hosts

### Database

The project uses PostgreSQL in Docker. SQLite is also supported for local development.

### Ollama Model

The application uses `sqlcoder-7b-2:Q4_K_M` model which is:
- Optimized for SQL generation
- Quantized to Q4_K_M for efficient inference
- ~4.5GB in size
- Runs entirely locally (no API keys needed)

## AI Agent

The application uses Ollama with the sqlcoder-7b-2 model for converting questions to SQL:

- **With Ollama**: Uses local LLM inference (default in Docker)
- **Fallback**: Uses simple pattern matching if Ollama is unavailable

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

## Development

For development, you can:

1. Add new models in `querycraft/models.py`
2. Modify SQL generation prompts in `querycraft/services.py`
3. Customize the UI in `querycraft/templates/querycraft/query_form.html`

## Troubleshooting

### Ollama model not loading

If queries fail, check if the model is loaded:
```bash
docker-compose exec ollama ollama list
```

If the model is not listed, pull it:
```bash
docker-compose exec ollama ollama pull sqlcoder-7b-2:Q4_K_M
```

### Ollama service not responding

Check Ollama logs:
```bash
docker-compose logs ollama
```

Restart the Ollama service:
```bash
docker-compose restart ollama
```

### Out of memory errors

The sqlcoder-7b-2:Q4_K_M model requires approximately 4-6GB RAM. If you encounter memory issues:
- Ensure Docker has enough memory allocated
- Consider using a smaller model variant
- Close other memory-intensive applications

## License

This project is free for educational and commercial use.

## Support

For issues and questions, please create an Issue.
