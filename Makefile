.PHONY: test lint format

# Define Python interpreter
PYTHON := uv run --project $$(pwd)
UV := uv --project $$(pwd)

# Default target
all: lint format mypy test build

init:
	$(UV) sync --dev

build:
	$(UV) build

# Run pytest for testing
test:
	$(PYTHON) -m pytest tests/ -v

# Run mypy for type checking
mypy:
	$(PYTHON) -m mypy .

# Run ruff for linting
lint:
	$(PYTHON) -m ruff check .

# Run black for formatting
format:
	$(PYTHON) -m ruff format .
	$(PYTHON) -m black .
	$(PYTHON) -m isort .

# Install dependencies
setup:
	uv pip install -e ".[dev]"

# Clean up cache files
clean:
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf __pycache__
	rm -rf */__pycache__
	rm -rf */*/__pycache__
	find . -name "*.pyc" -delete
