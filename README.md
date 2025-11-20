# QueryCraft 🔍

A Django web application that converts natural language questions to SQL queries using an AI Agent and extracts results from the database.

## Features

- ✨ Convert natural language questions to SQL using local LLM (Ollama)
- 🗄️ Support for SQLite and PostgreSQL
- 🐳 Fully Dockerized with 3 services (web, db, ollama)
- 🎨 Beautiful and modern UI
- 🔒 Secure and reliable with SQL validation
- 🤖 Local LLM inference with sqlcoder-7b-2 model
- 🔄 LangGraph workflow for SQL generation, validation, and execution

## Architecture

The project consists of 3 main Docker services:

1. **web** - Django application
2. **db** - PostgreSQL database
3. **ollama** - Local LLM service running `sqlcoder-7b-2:Q4_K_M` model

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

   **Note:** On first run, the Ollama service will automatically:

   - Download the custom GGUF model file from HuggingFace (~4.5GB)
   - Create a Modelfile for the model
   - Import the model into Ollama

   This process may take 10-15 minutes depending on your internet connection. The model will be cached in the `models/` directory and `ollama_data` volume for subsequent runs.

4. **Wait for model setup to complete**

   Monitor the Ollama service logs to see when the model is ready:

   ```bash
   docker-compose logs -f ollama
   ```

   You'll see messages like:

   - "Downloading model from..."
   - "Model downloaded successfully!"
   - "Model sqlcoder-7b-2:Q4_K_M imported successfully!"
   - "Setup complete! Model sqlcoder-7b-2:Q4_K_M is ready to use."

5. **Access the application**

   - Open your browser and navigate to:

   ```
   http://localhost:8000
   ```

6. **Create Django superuser (for Admin access)**

   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

7. **Seed the database with realistic data (recommended)**

   ```bash
   docker-compose exec web python manage.py seed_db
   ```

   This command uses Faker to create at least 1000 rows of realistic data:

   - 300 customers
   - 100 products
   - 1000 orders

   All referential integrity is maintained (orders reference valid customers and products).

   **Options:**

   ```bash
   # Customize the number of records
   docker-compose exec web python manage.py seed_db --customers 500 --products 200 --orders 2000

   # Clear existing data before seeding
   docker-compose exec web python manage.py seed_db --clear
   ```

8. **Create sample data (alternative - smaller dataset)**
   ```bash
   docker-compose exec web python manage.py create_sample_data
   ```
   This command creates 20 sample customers, 15 products, and 50 orders (for quick testing).

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
docker-compose exec web python manage.py seed_db
docker-compose exec web python manage.py shell

# Check if Ollama model is loaded
docker-compose exec ollama ollama list

# Check model status
docker-compose exec ollama ollama show sqlcoder-7b-2:Q4_K_M

# View Ollama logs (useful for debugging model setup)
docker-compose logs ollama
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

   # Download the custom GGUF model
   mkdir -p models
   curl -L -o models/sqlcoder-7b-2.Q4_K_M.gguf \
     https://huggingface.co/MaziyarPanahi/sqlcoder-7b-2-GGUF/resolve/main/sqlcoder-7b-2.Q4_K_M.gguf

   # Create Modelfile
   cat > Modelfile <<EOF
   FROM models/sqlcoder-7b-2.Q4_K_M.gguf

   PARAMETER temperature 0.3
   PARAMETER top_p 0.9
   PARAMETER top_k 40

   SYSTEM """You are a SQL expert who converts natural language questions to precise SQL queries. Always return only the SQL query without additional explanations."""
   EOF

   # Import model into Ollama
   ollama create sqlcoder-7b-2:Q4_K_M -f Modelfile
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

8. **Seed the database with realistic data (recommended)**

   ```bash
   uv run python manage.py seed_db
   ```

   This command uses Faker to create at least 1000 rows of realistic data.

   **Options:**

   ```bash
   # Customize the number of records
   uv run python manage.py seed_db --customers 500 --products 200 --orders 2000

   # Clear existing data before seeding
   uv run python manage.py seed_db --clear
   ```

9. **Create sample data (alternative - smaller dataset)**

   ```bash
   uv run python manage.py create_sample_data
   ```

   This creates 20 sample customers, 15 products, and 50 orders (for quick testing).

10. **Access the application**
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
├── querycraft_project/     # Main Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── querycraft/             # Main application
│   ├── models.py          # Database models (Customer, Product, Order)
│   ├── views.py           # Application views
│   ├── services.py        # AI Agent service (LangGraph + Ollama)
│   ├── urls.py            # URL routing
│   ├── admin.py           # Admin settings
│   └── templates/         # HTML templates
│       ├── query_form.html
│       └── api_client.html
├── models/                 # GGUF model storage (created on first run)
├── docker-compose.yml     # Docker Compose configuration (3 services)
├── Dockerfile             # Docker image for web service
├── Modelfile              # Ollama model configuration
├── init_ollama.sh         # Script to download and setup custom model
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

The application uses a custom `sqlcoder-7b-2:Q4_K_M` GGUF model which is:

- **Source**: Downloaded from HuggingFace (MaziyarPanahi/sqlcoder-7b-2-GGUF)
- **Format**: GGUF (not in Ollama repository)
- **Optimized for**: SQL generation from natural language
- **Quantization**: Q4_K_M for efficient inference
- **Size**: ~4.5GB
- **Setup**: Automatically downloaded and configured on first Docker run
- **Location**: Stored in `models/` directory and Ollama volume
- **Runs entirely locally**: No API keys needed

The model is automatically set up via the `init_ollama.sh` script which:

1. Downloads the GGUF file from HuggingFace
2. Creates a Modelfile with optimized parameters
3. Imports the model into Ollama

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

## Development

For development, you can:

1. Add new models in `querycraft/models.py`
2. Modify SQL generation prompts in `querycraft/services.py`
3. Customize the UI in `querycraft/templates/querycraft/query_form.html`
4. Seed the database with realistic test data:
   ```bash
   python manage.py seed_db --customers 500 --products 200 --orders 2000
   ```

### Code Quality Tools

The project uses **ruff** and **mypy** for code quality and type checking.

**Install development dependencies:**

```bash
uv sync --dev
```

**Run ruff (linting and formatting):**

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

**Run mypy (type checking):**

```bash
uv run mypy .
```

**Run both:**

```bash
uv run ruff check . && uv run ruff format . && uv run mypy .
```

### Database Seeding

The `seed_db` management command uses the Faker library to generate realistic test data:

- **Maintains Referential Integrity**: All foreign keys (customer_id, product_id) reference valid records
- **Realistic Data**: Uses Faker for names, emails, dates, and product names
- **Bulk Operations**: Uses bulk_create for efficient database operations
- **Configurable**: Customize the number of records per table via command-line arguments
- **Minimum 1000 Rows**: Automatically ensures at least 1000 total rows across all tables

**Usage:**

```bash
# Default: 300 customers, 100 products, 1000 orders (1400 total rows)
python manage.py seed_db

# Custom amounts
python manage.py seed_db --customers 500 --products 200 --orders 2000

# Clear existing data first
python manage.py seed_db --clear
```

## Troubleshooting

### Ollama model not loading

If queries fail, check if the model is loaded:

```bash
docker-compose exec ollama ollama list
```

If the model is not listed, check the Ollama logs:

```bash
docker-compose logs ollama
```

The model should be automatically set up on first run. If it failed:

1. Check if the model file was downloaded: `ls -lh models/sqlcoder-7b-2.Q4_K_M.gguf`
2. Manually run the setup script:
   ```bash
   docker-compose exec ollama /init_ollama.sh
   ```
3. Or manually import the model:
   ```bash
   docker-compose exec ollama ollama create sqlcoder-7b-2:Q4_K_M -f /tmp/Modelfile
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

- Ensure Docker has enough memory allocated (recommended: 8GB+)
- Consider using a smaller model variant or lower quantization
- Close other memory-intensive applications
- Check Docker memory settings: Docker Desktop → Settings → Resources

### Model download issues

If the model download fails:

- Check your internet connection
- The download may timeout on slow connections - try again
- You can manually download the model:
  ```bash
  mkdir -p models
  curl -L -o models/sqlcoder-7b-2.Q4_K_M.gguf \
    https://huggingface.co/MaziyarPanahi/sqlcoder-7b-2-GGUF/resolve/main/sqlcoder-7b-2.Q4_K_M.gguf
  ```
- Then restart the Ollama service: `docker-compose restart ollama`

## License

This project is free for educational and commercial use.

## Support

For issues and questions, please create an Issue.

User Question
|
v
[Node 1] SQL Generator (Ollama)
|
v
[Node 2] SQL Validator
|
|--- [valid?] ---> [Node 3] Execute SQL ---> return result
|
L--- [invalid?] -> return error message
