# ============================================
# Ollama LLM Service for QueryCraft
# ============================================
# This Dockerfile sets up an Ollama container with the sqlcoder-7b-2 model
# for converting natural language to SQL queries.
#
# IMPORTANT: Model Storage Strategy
# ----------------------------------
# The 4.5GB GGUF model (sqlcoder-7b-2.Q4_K_M.gguf) should be stored externally
# and mounted as a volume to avoid bloating the Docker image.
#
# Recommended setup:
# 1. Download the model once: ./init_ollama.sh (run on host)
# 2. Mount ./models directory as volume in docker-compose.yml
# 3. The container will detect and use the pre-downloaded model
#
# Volume mount: ./models:/app/models
# ============================================

FROM ollama/ollama:latest

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Create directory structure
RUN mkdir -p /app/models

# Copy Ollama model configuration
COPY Modelfile /app/Modelfile

# Copy initialization script (checks for model, creates if needed)
COPY init_ollama.sh /app/init_ollama.sh
RUN chmod +x /app/init_ollama.sh

# Copy entrypoint script (starts Ollama + loads model)
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose Ollama API port
EXPOSE 11434

# Health check to ensure Ollama is responsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=3 \
  CMD curl -f http://localhost:11434/api/tags || exit 1

# Use custom entrypoint for initialization
ENTRYPOINT ["/app/entrypoint.sh"]
