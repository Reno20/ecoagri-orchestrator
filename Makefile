# EcoAgri-Orchestrator Makefile
# ─────────────────────────────

.PHONY: install sync lint test playground clean

# Install dependencies
install:
	uv sync

# Sync dependencies (alias)
sync:
	uv sync

# Run linter
lint:
	uv run ruff check app/
	uv run ruff format --check app/

# Run tests
test:
	uv run pytest tests/ -v

# Launch ADK playground on port 18081
playground:
	uv run agents-cli playground --port 18081

# Clean up caches and build artifacts
clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache .adk/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
