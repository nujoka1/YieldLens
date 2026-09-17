.DEFAULT_GOAL := help
.PHONY: help setup validate up down restart ps logs test lint format check clean integration coverage pull

PYTHON ?= python3.12
COMPOSE ?= docker compose

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "%-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Create local environment configuration and Python virtual environment
	@test -f .env || $(PYTHON) scripts/init_env.py
	@test -d .venv || $(PYTHON) -m venv .venv
	.venv/bin/python -m pip install -r requirements-dev.txt

validate: ## Validate the fully rendered Compose model
	$(COMPOSE) config --quiet

up: ## Build and start the Phase 1 platform
	$(COMPOSE) build app
	@for service in postgres minio kafka spark-master spark-worker app; do \
		$(COMPOSE) up -d --no-build --wait --wait-timeout 300 $$service || exit 1; \
	done

pull: ## Pull required service images
	$(COMPOSE) pull

down: ## Stop containers without deleting persistent volumes
	$(COMPOSE) down

restart: down up ## Restart the platform

ps: ## Show container and health status
	$(COMPOSE) ps

logs: ## Follow logs from all services
	$(COMPOSE) logs --follow --tail=200

test: ## Run unit tests with coverage
	PYTHONPATH=src .venv/bin/python -m pytest --cov-report=html --cov-report=term-missing

lint: ## Check Python formatting and static rules
	.venv/bin/python -m ruff check src tests scripts
	.venv/bin/python -m ruff format --check src tests scripts

format: ## Apply Python formatting and safe lint fixes
	.venv/bin/python -m ruff check --fix src tests scripts
	.venv/bin/python -m ruff format src tests scripts

integration: ## Run real service tests and the synthetic end-to-end probe
	YIELDLENS_INTEGRATION=1 PYTHONPATH=src .venv/bin/python -m pytest -s --cov-report=html --cov-report=term-missing

coverage: ## Combine Python 3.12 unit and app probe coverage after integration
	$(COMPOSE) exec -T app python -m coverage run -p --source=/app/src -m pytest -o addopts= -p no:cacheprovider /app/tests
	$(COMPOSE) exec -T app python -m coverage run -p --source=/app/src -m yieldlens.healthcheck
	$(COMPOSE) exec -T app python -m coverage combine --keep
	$(COMPOSE) exec -T app python -m coverage report -m
	$(COMPOSE) exec -T app python -m coverage html -d /tmp/coverage-html
	mkdir -p htmlcov
	$(COMPOSE) cp app:/tmp/coverage-html/. htmlcov/

check: validate lint test ## Run all Phase 1 checks

clean: ## Remove local Python caches only; Docker volumes are preserved
	find src tests -type d -name __pycache__ -prune -exec rm -r {} +
	find src tests -type f -name '*.pyc' -delete
