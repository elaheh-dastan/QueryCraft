#!/bin/bash
set -e

echo "========================================="
echo "QueryCraft Ollama Service Startup"
echo "========================================="

# Trap signals for graceful shutdown
trap 'echo "Shutting down Ollama..."; kill $OLLAMA_PID 2>/dev/null; exit 0' SIGTERM SIGINT

# Start Ollama service in background
echo "Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama API to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  if curl -s -f http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "✓ Ollama is ready!"
    break
  fi

  RETRY_COUNT=$((RETRY_COUNT + 1))

  if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "✗ Error: Ollama failed to start after ${MAX_RETRIES} attempts"
    kill $OLLAMA_PID 2>/dev/null || true
    exit 1
  fi

  echo "  Waiting for Ollama... ($RETRY_COUNT/$MAX_RETRIES)"
  sleep 2
done

# Run initialization script (model setup)
echo ""
echo "Running Ollama initialization..."
if /app/init_ollama.sh; then
  echo "✓ Initialization completed successfully"
else
  echo "✗ Warning: Initialization script failed (exit code: $?)"
  echo "  The service will continue, but the model may not be available."
fi

# Verify model is loaded
echo ""
echo "Verifying model availability..."
if curl -s http://localhost:11434/api/tags | grep -q "sqlcoder"; then
  echo "✓ sqlcoder model is loaded and ready"
else
  echo "⚠ Warning: sqlcoder model not found in loaded models"
  echo "  You may need to manually run: ollama create sqlcoder -f /app/Modelfile"
fi

echo ""
echo "========================================="
echo "Ollama service is running"
echo "API endpoint: http://localhost:11434"
echo "========================================="
echo ""

# Keep Ollama running in foreground (wait for the background process)
wait $OLLAMA_PID
