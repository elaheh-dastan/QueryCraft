#!/bin/sh
set -e

# Start Ollama in background
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
for i in $(seq 1 30); do
  if curl -f http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "Ollama is ready!"
    break
  fi
  if [ $i -eq 30 ]; then
    echo "Error: Ollama failed to start"
    exit 1
  fi
  echo "Waiting for Ollama... ($i/30)"
  sleep 2
done

# Run initialization script
/app/init_ollama.sh

# Keep Ollama running
wait $OLLAMA_PID

