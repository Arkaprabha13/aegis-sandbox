COMPOSE = docker compose -f sandbox/docker-compose.yml

.PHONY: help install up down build smoke attack test clean logs

help:
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-10s %s\n", $$1, $$2}'

install: ## Install host-side deps
	pip install -r requirements-dev.txt

up: ## Start sandbox
	$(COMPOSE) up -d --build

down: ## Stop sandbox and wipe volume
	$(COMPOSE) down -v

build: ## Build sandbox images
	$(COMPOSE) build

smoke: ## Run smoke test
	bash smoke_test.sh

attack: ## Run one attack campaign
	python redteam/run.py --target http://127.0.0.1:8000 --max-attempts 5

test: ## Run regression suite
	python tests/run_regression.py

logs: ## Tail sandbox logs
	$(COMPOSE) logs -f

clean: down ## Full reset including telemetry
	rm -f telemetry/aegis.db telemetry/aegis.db-wal telemetry/aegis.db-shm
