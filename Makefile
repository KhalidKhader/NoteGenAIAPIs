# Makefile for NoteGen AI APIs - Medical SOAP Generation Microservice
# Production-ready development automation

.PHONY: install dev test lint format clean docker-up docker-down help
.DEFAULT_GOAL := help

# Colors for output formatting
BOLD := \033[1m
CYAN := \033[96m
GREEN := \033[92m
YELLOW := \033[93m
RED := \033[91m
RESET := \033[0m

# Project Configuration
PROJECT_NAME := notegen-ai-apis
PYTHON_VERSION := 3.11
DOCKER_COMPOSE_FILE := docker-compose.yml

## Development Commands

install: ## Install dependencies and setup development environment
	@echo "$(CYAN)Installing dependencies with Poetry...$(RESET)"
	poetry install --with dev
	@echo "$(GREEN)✓ Dependencies installed successfully$(RESET)"
	@echo "$(YELLOW)Setting up pre-commit hooks...$(RESET)"
	poetry run pre-commit install
	@echo "$(GREEN)✓ Pre-commit hooks installed$(RESET)"

dev-setup: ## Complete development environment setup
	@echo "$(BOLD)$(CYAN)Setting up NoteGen AI APIs development environment...$(RESET)"
	@echo "$(YELLOW)Step 1: Installing Poetry dependencies...$(RESET)"
	$(MAKE) install
	@echo "$(YELLOW)Step 2: Setting up environment variables...$(RESET)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Creating .env file from template...$(RESET)"; \
		cp .env.example .env; \
		echo "$(RED)⚠️  Please update .env with your actual configuration$(RESET)"; \
	fi
	@echo "$(YELLOW)Step 3: Starting Docker services...$(RESET)"
	$(MAKE) docker-up
	@echo "$(GREEN)$(BOLD)✓ Development environment ready!$(RESET)"
	@echo "$(CYAN)Next steps:$(RESET)"
	@echo "  1. Update .env with your API keys"
	@echo "  2. Run: make dev"
	@echo "  3. Visit: http://localhost:8000/docs"

dev: ## Start development server with hot reload
	@echo "$(CYAN)Starting development server...$(RESET)"
	poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

dev-reset: ## Reset development environment
	@echo "$(YELLOW)Resetting development environment...$(RESET)"
	$(MAKE) clean
	$(MAKE) docker-down
	poetry env remove --all
	$(MAKE) dev-setup

## Testing Commands

test: ## Run all tests
	@echo "$(CYAN)Running all tests...$(RESET)"
	poetry run pytest tests/ -v

test-unit: ## Run unit tests only
	@echo "$(CYAN)Running unit tests...$(RESET)"
	poetry run pytest tests/unit/ -v

test-integration: ## Run integration tests only
	@echo "$(CYAN)Running integration tests...$(RESET)"
	poetry run pytest tests/integration/ -v

test-cov: ## Run tests with coverage report
	@echo "$(CYAN)Running tests with coverage...$(RESET)"
	poetry run pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/$(RESET)"

test-watch: ## Run tests in watch mode
	@echo "$(CYAN)Running tests in watch mode...$(RESET)"
	poetry run pytest-watch tests/ src/

perf-test: ## Run performance tests
	@echo "$(CYAN)Running performance tests...$(RESET)"
	poetry run pytest tests/performance/ -v

load-test: ## Run load tests with Locust
	@echo "$(CYAN)Starting load tests...$(RESET)"
	poetry run locust --config tests/locust.conf

## Code Quality Commands

lint: ## Run all linting checks
	@echo "$(CYAN)Running linting checks...$(RESET)"
	poetry run ruff check src/ tests/
	poetry run mypy src/
	@echo "$(GREEN)✓ Linting completed$(RESET)"

format: ## Format code with black and isort
	@echo "$(CYAN)Formatting code...$(RESET)"
	poetry run black src/ tests/
	poetry run isort src/ tests/
	@echo "$(GREEN)✓ Code formatted$(RESET)"

format-check: ## Check code formatting without applying changes
	@echo "$(CYAN)Checking code formatting...$(RESET)"
	poetry run black --check src/ tests/
	poetry run isort --check-only src/ tests/

security: ## Run security scans
	@echo "$(CYAN)Running security scans...$(RESET)"
	poetry run bandit -r src/
	poetry run safety check --json
	@echo "$(GREEN)✓ Security scan completed$(RESET)"

audit: ## Audit dependencies for vulnerabilities
	@echo "$(CYAN)Auditing dependencies...$(RESET)"
	poetry audit
	@echo "$(GREEN)✓ Dependency audit completed$(RESET)"

check: ## Run all quality checks
	@echo "$(BOLD)$(CYAN)Running comprehensive quality checks...$(RESET)"
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) security
	$(MAKE) test-cov
	@echo "$(GREEN)$(BOLD)✓ All quality checks passed!$(RESET)"

## Docker Commands

docker-up: ## Start Docker services (Neo4j, Vector DB)
	@echo "$(CYAN)Starting Docker services...$(RESET)"
	docker-compose up -d
	@echo "$(GREEN)✓ Docker services started$(RESET)"
	@echo "$(YELLOW)Neo4j Browser: http://localhost:7474$(RESET)"

docker-down: ## Stop Docker services
	@echo "$(CYAN)Stopping Docker services...$(RESET)"
	docker-compose down
	@echo "$(GREEN)✓ Docker services stopped$(RESET)"

docker-logs: ## View Docker service logs
	@echo "$(CYAN)Viewing Docker service logs...$(RESET)"
	docker-compose logs -f

docker-rebuild: ## Rebuild Docker services
	@echo "$(CYAN)Rebuilding Docker services...$(RESET)"
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

## Database Commands

db-setup: ## Initialize databases with sample data
	@echo "$(CYAN)Setting up databases...$(RESET)"
	poetry run python scripts/setup_databases.py
	@echo "$(GREEN)✓ Databases initialized$(RESET)"

db-migrate: ## Run database migrations
	@echo "$(CYAN)Running database migrations...$(RESET)"
	poetry run python scripts/migrate_databases.py
	@echo "$(GREEN)✓ Database migrations completed$(RESET)"

db-seed: ## Seed databases with test data
	@echo "$(CYAN)Seeding databases with test data...$(RESET)"
	poetry run python scripts/seed_test_data.py
	@echo "$(GREEN)✓ Test data seeded$(RESET)"

## Neo4j Commands

neo4j-status: ## Check Neo4j status
	@echo "$(CYAN)Checking Neo4j status...$(RESET)"
	docker ps | grep neo4j

neo4j-connect: ## Connect to Neo4j shell
	@echo "$(CYAN)Connecting to Neo4j shell...$(RESET)"
	docker exec -it neo4j-container cypher-shell -u neo4j

neo4j-logs: ## View Neo4j logs
	@echo "$(CYAN)Viewing Neo4j logs...$(RESET)"
	docker logs neo4j-container

neo4j-backup: ## Backup Neo4j database
	@echo "$(CYAN)Creating Neo4j backup...$(RESET)"
	docker exec neo4j-container neo4j-admin dump --database=neo4j --to=/backups/neo4j-backup.dump
	@echo "$(GREEN)✓ Neo4j backup created$(RESET)"

## Health and Monitoring Commands

health-check: ## Run comprehensive health checks
	@echo "$(CYAN)Running health checks...$(RESET)"
	@echo "$(YELLOW)Checking API health...$(RESET)"
	curl -f http://localhost:8000/health || echo "$(RED)API health check failed$(RESET)"
	@echo "$(YELLOW)Checking Neo4j connection...$(RESET)"
	$(MAKE) neo4j-status
	@echo "$(YELLOW)Checking vector database...$(RESET)"
	poetry run python scripts/check_vector_db.py
	@echo "$(GREEN)✓ Health checks completed$(RESET)"

monitor: ## Start monitoring dashboard
	@echo "$(CYAN)Starting monitoring dashboard...$(RESET)"
	poetry run python scripts/monitoring_dashboard.py

metrics: ## View system metrics
	@echo "$(CYAN)Displaying system metrics...$(RESET)"
	curl -s http://localhost:8000/metrics | grep -E "(soap_|rag_|llm_)"

## Deployment Commands

deploy-check: ## Run pre-deployment checks
	@echo "$(BOLD)$(CYAN)Running pre-deployment checks...$(RESET)"
	@echo "$(YELLOW)1. Code quality checks...$(RESET)"
	$(MAKE) check
	@echo "$(YELLOW)2. Security validation...$(RESET)"
	$(MAKE) security
	@echo "$(YELLOW)3. Performance tests...$(RESET)"
	$(MAKE) perf-test
	@echo "$(YELLOW)4. Health checks...$(RESET)"
	$(MAKE) health-check
	@echo "$(GREEN)$(BOLD)✓ All deployment checks passed!$(RESET)"

build: ## Build production Docker image
	@echo "$(CYAN)Building production Docker image...$(RESET)"
	docker build -t $(PROJECT_NAME):latest .
	@echo "$(GREEN)✓ Production image built$(RESET)"

## Utility Commands

clean: ## Clean cache and temporary files
	@echo "$(CYAN)Cleaning cache and temporary files...$(RESET)"
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "htmlcov" -delete
	find . -type d -name ".mypy_cache" -delete
	find . -type d -name ".ruff_cache" -delete
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	@echo "$(GREEN)✓ Cleanup completed$(RESET)"

deps-update: ## Update all dependencies
	@echo "$(CYAN)Updating dependencies...$(RESET)"
	poetry update
	@echo "$(GREEN)✓ Dependencies updated$(RESET)"

deps-export: ## Export dependencies to requirements.txt
	@echo "$(CYAN)Exporting dependencies...$(RESET)"
	poetry export -f requirements.txt --output requirements.txt --without-hashes
	poetry export -f requirements.txt --output requirements-dev.txt --with dev --without-hashes
	@echo "$(GREEN)✓ Dependencies exported$(RESET)"

deps-check: ## Check for outdated dependencies
	@echo "$(CYAN)Checking for outdated dependencies...$(RESET)"
	poetry show --outdated

shell: ## Open Poetry shell
	@echo "$(CYAN)Opening Poetry shell...$(RESET)"
	poetry shell

env-info: ## Show environment information
	@echo "$(BOLD)$(CYAN)Environment Information:$(RESET)"
	@echo "$(YELLOW)Python Version:$(RESET)" $(shell poetry run python --version)
	@echo "$(YELLOW)Poetry Version:$(RESET)" $(shell poetry --version)
	@echo "$(YELLOW)Virtual Environment:$(RESET)" $(shell poetry env info --path)
	@echo "$(YELLOW)Dependencies:$(RESET)" $(shell poetry show --tree | head -10)

## Documentation Commands

docs-build: ## Build documentation
	@echo "$(CYAN)Building documentation...$(RESET)"
	poetry run mkdocs build
	@echo "$(GREEN)✓ Documentation built$(RESET)"

docs-serve: ## Serve documentation locally
	@echo "$(CYAN)Serving documentation at http://localhost:8001...$(RESET)"
	poetry run mkdocs serve --dev-addr localhost:8001

docs-deploy: ## Deploy documentation
	@echo "$(CYAN)Deploying documentation...$(RESET)"
	poetry run mkdocs gh-deploy
	@echo "$(GREEN)✓ Documentation deployed$(RESET)"

## Mock testing commands
test-mock:
	poetry run python tests/mock_testing/run_all_tests.py --type mock

test-mock-quick:
	poetry run python tests/mock_testing/run_all_tests.py --quick

test-scenarios:
	poetry run python tests/mock_testing/run_all_tests.py --type scenarios

test-performance:
	poetry run python tests/mock_testing/run_all_tests.py --type performance

test-comprehensive:
	poetry run python tests/mock_testing/run_all_tests.py --type all

# Run specific mock tests
test-soap-storage:
	poetry run pytest tests/mock_testing/test_soap_generation_with_storage.py -v

test-api-storage:
	poetry run pytest tests/mock_testing/test_api_integration_with_storage.py -v

# Test with long conversation data
test-longconv:
	poetry run pytest tests/mock_testing/ -k "long" -v -s

## Help

help: ## Show this help message
	@echo "$(BOLD)$(CYAN)NoteGen AI APIs - Medical SOAP Generation Microservice$(RESET)"
	@echo "$(CYAN)Available commands:$(RESET)"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo
	@echo "$(YELLOW)Quick Start:$(RESET)"
	@echo "  1. make dev-setup     # Setup development environment"
	@echo "  2. make dev          # Start development server"
	@echo "  3. make test         # Run tests"
	@echo
	@echo "$(YELLOW)Documentation:$(RESET)"
	@echo "  • API Docs: http://localhost:8000/docs"
	@echo "  • Neo4j Browser: http://localhost:7474"
	@echo "  • LangFuse: https://us.cloud.langfuse.com"
