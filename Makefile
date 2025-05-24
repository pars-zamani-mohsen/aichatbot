.PHONY: install test lint format clean docker-build docker-up docker-down migrate

install:
	pip install -r requirements.txt

test:
	pytest

lint:
	flake8 app tests
	mypy app tests
	black --check app tests
	isort --check-only app tests

format:
	black app tests
	isort app tests

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".coverage" -exec rm -r {} +
	find . -type d -name "htmlcov" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
	find . -type d -name ".ruff_cache" -exec rm -r {} +

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

migrate:
	alembic upgrade head

migrate-rollback:
	alembic downgrade -1

migrate-create:
	alembic revision --autogenerate -m "$(message)"

help:
	@echo "Available commands:"
	@echo "  install         - Install dependencies"
	@echo "  test           - Run tests"
	@echo "  lint           - Run linters"
	@echo "  format         - Format code"
	@echo "  clean          - Clean cache files"
	@echo "  docker-build   - Build Docker images"
	@echo "  docker-up      - Start Docker containers"
	@echo "  docker-down    - Stop Docker containers"
	@echo "  migrate        - Run database migrations"
	@echo "  migrate-rollback - Rollback last migration"
	@echo "  migrate-create - Create new migration"
	@echo "  help           - Show this help message" 