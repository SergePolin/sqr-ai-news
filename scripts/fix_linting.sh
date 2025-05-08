#!/bin/bash

# Fix linting issues automatically using ruff
echo "Running ruff to fix linting issues..."
poetry run ruff check --fix app tests

# Format the code with black
echo "Running black formatter..."
poetry run black app tests

# Run isort to fix imports
echo "Running isort to fix imports..."
poetry run isort app tests

echo "Linting fixes completed! Run 'git diff' to see changes." 