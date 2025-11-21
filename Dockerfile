FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/app/.venv/bin:$PATH"

# Set work directory
WORKDIR /app

# Install system dependencies needed for building Python packages
RUN apt-get update && apt-get install -y \
  gcc curl \
  && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy dependency files for caching
COPY pyproject.toml uv.lock ./

# Build argument to control dev/prod dependencies
ARG DEV_MODE=false

# Install Python dependencies (conditionally include dev dependencies)
RUN if [ "$DEV_MODE" = "true" ]; then \
  uv sync --frozen; \
  else \
  uv sync --no-dev --frozen; \
  fi

# Set work directory
WORKDIR /app

# Copy application code
COPY . .

# Copy entrypoint script and set execute permissions
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8000

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Use entrypoint script for initialization
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (can be overridden)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
