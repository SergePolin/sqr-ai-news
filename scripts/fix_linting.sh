#!/bin/bash

# Fix linting issues automatically using ruff
echo "Running ruff to fix linting issues..."
poetry run ruff check --fix app tests

# Fix flake8 specific issues that ruff might miss
echo "Running flake8 to identify remaining issues..."
poetry run flake8 app tests --exit-zero

# Run isort to fix imports (this will remove unused imports)
echo "Running isort to fix imports..."
poetry run isort app tests

# Format the code with black
echo "Running black formatter..."
poetry run black app tests

echo "Linting fixes completed! Run 'git diff' to see changes."
echo "Note: Some unused imports might need manual removal if isort didn't handle them."