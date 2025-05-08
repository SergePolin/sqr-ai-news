.PHONY: install run test clean lint docker-build docker-run docker-up docker-down

install:
	poetry install

activate:
	poetry shell

run:
	poetry run python run.py

test:
	poetry run pytest

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete

lint:
	poetry run ruff check app tests

fix-lint:
	./scripts/fix_linting.sh

docker-build:
	docker build -t sqr-ai-news .

docker-run:
	docker run -p 8000:8000 sqr-ai-news

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down
