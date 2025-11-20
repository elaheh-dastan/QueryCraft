# ============================================
# Stage 1: Builder - Install dependencies
# ============================================
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies needed for building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
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

# ============================================
# Stage 2: Runtime - Minimal production image
# ============================================
FROM python:3.11-slim AS runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/app/.venv/bin:$PATH"

# Set work directory
WORKDIR /app

# Install only runtime system dependencies (no gcc)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash django && \
    mkdir -p /app/staticfiles /app/media && \
    chown -R django:django /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=django:django /app/.venv /app/.venv

# Copy application code
COPY --chown=django:django . .

# Switch to non-root user
USER django

# Expose port
EXPOSE 8000

# Copy and set entrypoint
COPY --chown=django:django entrypoint.sh /app/entrypoint.sh
USER root
RUN chmod +x /app/entrypoint.sh
USER django

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Use entrypoint script for initialization
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (can be overridden)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
