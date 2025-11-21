#!/bin/sh
# Script to download and setup custom GGUF model for Ollama

set -e

MODEL_URL="https://huggingface.co/MaziyarPanahi/sqlcoder-7b-2-GGUF/resolve/main/sqlcoder-7b-2.Q4_K_M.gguf"
MODEL_NAME="sqlcoder-7b-2:local"
MODEL_FILE="/models/sqlcoder-7b-2.Q4_K_M.gguf"
MODEL_DIR="/models"

echo "Waiting for Ollama to be ready..."
until curl -f http://localhost:11434/api/tags >/dev/null 2>&1; do
	echo "Ollama is not ready yet. Waiting..."
	sleep 2
done

echo "Ollama is ready!"

# Create models directory if it doesn't exist
mkdir -p "$MODEL_DIR"

# Check if model is already imported (may have been imported during build)
if ollama list | grep -q "$MODEL_NAME"; then
	echo "Model $MODEL_NAME is already imported (from Docker build or previous run)"
else
	echo "Model not found, importing now..."
	echo "Using Modelfile from /app/Modelfile"

	echo "Importing model into Ollama..."
	ollama create "$MODEL_NAME" || {
		echo "Error: Failed to import model"
		exit 1
	}

	echo "Model $MODEL_NAME imported successfully!"
fi

echo "Setup complete! Model $MODEL_NAME is ready to use."
