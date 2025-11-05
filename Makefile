.PHONY: help setup install format lint typecheck test test-unit test-integration test-e2e audit bench serve clean docker-build docker-up docker-down pre-commit-install pre-commit-run migration-create migration-upgrade migration-downgrade

# Default target - show help
.DEFAULT_GOAL := help

# ANSI color codes for pretty output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@echo "$(CYAN)NilAI Development Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(CYAN)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(GREEN)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup & Installation

setup: install pre-commit-install ## Complete project setup (install deps + pre-commit)
	@echo "$(GREEN)✓ Setup complete!$(NC)"
	@echo "$(CYAN)Next steps:$(NC)"
	@echo "  1. Copy .env.sample to .env and configure"
	@echo "  2. Run: make migration-upgrade"
	@echo "  3. Run: make serve"

install: ## Install all dependencies using uv
	@echo "$(CYAN)Installing dependencies...$(NC)"
	uv sync
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

pre-commit-install: ## Install pre-commit hooks
	@echo "$(CYAN)Installing pre-commit hooks...$(NC)"
	uv run pre-commit install --install-hooks
	uv run pre-commit install --hook-type commit-msg
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"

pre-commit-run: ## Run pre-commit hooks on all files
	@echo "$(CYAN)Running pre-commit hooks...$(NC)"
	uv run pre-commit run --all-files

##@ Code Quality

format: ## Format code with ruff
	@echo "$(CYAN)Formatting code...$(NC)"
	uv run ruff format .
	@echo "$(GREEN)✓ Code formatted$(NC)"

lint: ## Lint code with ruff
	@echo "$(CYAN)Linting code...$(NC)"
	uv run ruff check . --fix
	@echo "$(GREEN)✓ Linting complete$(NC)"

lint-check: ## Check linting without fixing
	@echo "$(CYAN)Checking linting...$(NC)"
	uv run ruff check .

typecheck: ## Run type checking with pyright
	@echo "$(CYAN)Type checking...$(NC)"
	uv run pyright
	@echo "$(GREEN)✓ Type checking complete$(NC)"

##@ Testing

test: ## Run all tests (unit + integration)
	@echo "$(CYAN)Running all tests...$(NC)"
	uv run pytest -v tests/unit tests/integration
	@echo "$(GREEN)✓ All tests passed$(NC)"

test-unit: ## Run unit tests only
	@echo "$(CYAN)Running unit tests...$(NC)"
	uv run pytest -v tests/unit
	@echo "$(GREEN)✓ Unit tests passed$(NC)"

test-integration: ## Run integration tests only
	@echo "$(CYAN)Running integration tests...$(NC)"
	uv run pytest -v tests/integration
	@echo "$(GREEN)✓ Integration tests passed$(NC)"

test-e2e: ## Run end-to-end tests (requires GPU)
	@echo "$(CYAN)Running E2E tests...$(NC)"
	uv run pytest -v tests/e2e
	@echo "$(GREEN)✓ E2E tests passed$(NC)"

test-cov: ## Run tests with coverage report
	@echo "$(CYAN)Running tests with coverage...$(NC)"
	uv run pytest -v --cov=nilai_api --cov=nilai_models --cov=nilai_common --cov-report=html --cov-report=term tests/unit tests/integration
	@echo "$(GREEN)✓ Coverage report generated: htmlcov/index.html$(NC)"

bench: ## Run performance benchmarks
	@echo "$(CYAN)Running benchmarks...$(NC)"
	uv run pytest -v tests/benchmarks --benchmark-only
	@echo "$(GREEN)✓ Benchmarks complete$(NC)"

##@ Security

audit: audit-deps audit-code ## Run all security audits (dependencies + code)

audit-deps: ## Audit dependencies for vulnerabilities
	@echo "$(CYAN)Auditing dependencies...$(NC)"
	uv run pip-audit --desc --skip-editable
	@echo "$(GREEN)✓ Dependency audit complete$(NC)"

audit-code: ## Audit code for security issues with bandit
	@echo "$(CYAN)Auditing code for security issues...$(NC)"
	uv run bandit -r nilai-api/src nilai-models/src packages/nilai-common/src -f screen --severity-level medium
	@echo "$(GREEN)✓ Code audit complete$(NC)"

audit-secrets: ## Scan for secrets in codebase
	@echo "$(CYAN)Scanning for secrets...$(NC)"
	uv run detect-secrets scan --baseline .secrets.baseline
	@echo "$(GREEN)✓ Secret scan complete$(NC)"

##@ Database

migration-create: ## Create a new database migration (use: make migration-create MSG="description")
ifndef MSG
	@echo "$(RED)Error: MSG variable required$(NC)"
	@echo "Usage: make migration-create MSG=\"your migration description\""
	@exit 1
endif
	@echo "$(CYAN)Creating migration: $(MSG)$(NC)"
	cd nilai-api && uv run alembic revision --autogenerate -m "$(MSG)"
	@echo "$(GREEN)✓ Migration created$(NC)"

migration-upgrade: ## Upgrade database to latest migration
	@echo "$(CYAN)Upgrading database...$(NC)"
	cd nilai-api && uv run alembic upgrade head
	@echo "$(GREEN)✓ Database upgraded$(NC)"

migration-downgrade: ## Downgrade database by one migration
	@echo "$(CYAN)Downgrading database...$(NC)"
	cd nilai-api && uv run alembic downgrade -1
	@echo "$(YELLOW)⚠ Database downgraded$(NC)"

migration-history: ## Show migration history
	@echo "$(CYAN)Migration history:$(NC)"
	cd nilai-api && uv run alembic history

##@ Development

serve: ## Start the FastAPI development server
	@echo "$(CYAN)Starting development server...$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"
	cd nilai-api && uv run uvicorn nilai_api.app:app --host 0.0.0.0 --port 8080 --reload

serve-prod: ## Start the production server with gunicorn
	@echo "$(CYAN)Starting production server...$(NC)"
	cd nilai-api && uv run gunicorn nilai_api.app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080

##@ Docker

docker-build: ## Build all Docker images
	@echo "$(CYAN)Building Docker images...$(NC)"
	docker-compose -f docker-compose.yml build
	@echo "$(GREEN)✓ Docker images built$(NC)"

docker-up: ## Start all services with docker-compose
	@echo "$(CYAN)Starting services...$(NC)"
	docker-compose -f docker-compose.yml up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo "$(CYAN)View logs: docker-compose logs -f$(NC)"

docker-down: ## Stop all services
	@echo "$(CYAN)Stopping services...$(NC)"
	docker-compose -f docker-compose.yml down
	@echo "$(GREEN)✓ Services stopped$(NC)"

docker-logs: ## View docker-compose logs
	docker-compose -f docker-compose.yml logs -f

docker-ps: ## Show running containers
	docker-compose -f docker-compose.yml ps

##@ CI/CD

ci: format lint-check typecheck test-unit audit ## Run all CI checks locally
	@echo "$(GREEN)✓✓✓ All CI checks passed! ✓✓✓$(NC)"

ci-full: format lint-check typecheck test audit bench ## Run complete CI pipeline
	@echo "$(GREEN)✓✓✓ Complete CI pipeline passed! ✓✓✓$(NC)"

##@ Cleanup

clean: ## Clean generated files and caches
	@echo "$(CYAN)Cleaning...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage build/ dist/
	@echo "$(GREEN)✓ Cleaned$(NC)"

clean-all: clean ## Clean everything including .venv
	@echo "$(YELLOW)Removing virtual environment...$(NC)"
	rm -rf .venv
	@echo "$(GREEN)✓ Deep clean complete$(NC)"

##@ Utilities

check-env: ## Check if .env file exists and is configured
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found$(NC)"; \
		echo "$(CYAN)Copy .env.sample to .env and configure it$(NC)"; \
		exit 1; \
	else \
		echo "$(GREEN)✓ .env file found$(NC)"; \
	fi

version: ## Show versions of key tools
	@echo "$(CYAN)Tool Versions:$(NC)"
	@echo "  Python:  $$(python --version 2>&1 | cut -d' ' -f2)"
	@echo "  uv:      $$(uv --version 2>&1 | cut -d' ' -f2)"
	@echo "  ruff:    $$(uv run ruff --version 2>&1 | cut -d' ' -f2)"
	@echo "  pyright: $$(uv run pyright --version 2>&1 | grep -oP '[\d.]+')"
	@echo "  pytest:  $$(uv run pytest --version 2>&1 | grep -oP '[\d.]+')"

deps-update: ## Update dependencies to latest versions
	@echo "$(CYAN)Updating dependencies...$(NC)"
	uv sync --upgrade
	@echo "$(GREEN)✓ Dependencies updated$(NC)"
	@echo "$(YELLOW)⚠ Remember to test after updating!$(NC)"

deps-tree: ## Show dependency tree
	@echo "$(CYAN)Dependency tree:$(NC)"
	uv tree

##@ Quick Commands (shortcuts)

f: format ## Shortcut for format
l: lint ## Shortcut for lint
t: test-unit ## Shortcut for test-unit
s: serve ## Shortcut for serve
