# QueryCraft 🔍

A Django web application that converts natural language questions to SQL queries using an AI Agent and extracts results from the database.

## Features

- ✨ Convert natural language questions to SQL using AI
- 🗄️ Support for SQLite and PostgreSQL
- 🐳 Fully Dockerized
- 🎨 Beautiful and modern UI
- 🔒 Secure and reliable

## Setup with Docker (Recommended)

### Prerequisites

- Docker
- Docker Compose

### Setup Steps

1. **Clone or download the project**

2. **Create `.env` file (optional)**
   ```bash
   cp .env.example .env
   ```
   
   Then edit the `.env` file and add your `OPENAI_API_KEY` (optional - for better results)

3. **Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

5. **Create Django superuser (for Admin access)**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

6. **Create sample data (optional)**
   ```bash
   docker-compose exec web python manage.py create_sample_data
   ```
   This command creates 20 sample users and 50 sample orders.

### Useful Docker Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Run Django commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py shell
```

## Setup without Docker (Local Development)

### Prerequisites

- Python 3.8+
- uv (install with pipx)

### Setup Steps

1. **Install `uv`**
   ```bash
   pipx install uv
   ```

2. **Install dependencies**
   ```bash
   uv pip install -e .
   ```

3. **Run migrations**
   ```bash
   uv run python manage.py migrate
   ```

4. **Create superuser (optional)**
   ```bash
   uv run python manage.py createsuperuser
   ```

5. **Run development server**
   ```bash
   uv run python manage.py runserver
   ```

6. **Create sample data (optional)**
   ```bash
   uv run python manage.py create_sample_data
   ```

7. **Access the application**
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
│   ├── models.py          # Database models (User, Order)
│   ├── views.py           # Application views
│   ├── services.py        # AI Agent service
│   ├── urls.py            # URL routing
│   ├── admin.py           # Admin settings
│   └── templates/         # HTML templates
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile             # Docker image
├── pyproject.toml         # Project dependencies
└── manage.py              # Django management script
```

## Configuration

### Environment Variables

- `DEBUG`: Debug mode (default: 1)
- `SECRET_KEY`: Django secret key
- `OPENAI_API_KEY`: OpenAI API key (optional - for better results)
- `DATABASE_URL`: Database URL (for PostgreSQL)
- `ALLOWED_HOSTS`: Allowed hosts

### Database

The project uses SQLite by default. PostgreSQL is also supported in Docker.

## AI Agent

The application uses an AI Agent to convert questions to SQL:

- **With OpenAI API**: If `OPENAI_API_KEY` is set, it uses GPT-3.5-turbo
- **Without API**: Uses a simple pattern matching system

## Example Questions

- "How many new users registered last month?"
- "Show all users"
- "What is the total number of orders?"
- "Users who registered in the past week"

## Development

For development, you can:

1. Add new models in `querycraft/models.py`
2. Add new SQL patterns in `querycraft/services.py`
3. Customize the UI in `querycraft/templates/querycraft/query_form.html`

## License

This project is free for educational and commercial use.

## Support

For issues and questions, please create an Issue.
