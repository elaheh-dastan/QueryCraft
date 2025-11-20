@default:
    @just --list

# Sync dependencies from pyproject.toml
sync:
    uv sync

# Upgrade all packages to latest versions
upgrade:
    uv lock --upgrade
    uv sync

# Run linting and type checking
lint:
    uv run ruff check --fix .
    uv run ruff format .
    uv run mypy .

[working-directory("models")]
download-model:
    wget 'https://huggingface.co/MaziyarPanahi/sqlcoder-7b-2-GGUF/resolve/main/sqlcoder-7b-2.Q4_K_M.gguf'
