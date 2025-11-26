.PHONY: help build up down restart logs clean test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build all Docker images
	docker-compose build

build-prod: ## Build production Docker images
	docker-compose -f docker-compose.prod.yml build

up: ## Start all services (development)
	docker-compose -f docker-compose.dev.yml up -d

up-prod: ## Start all services (production)
	docker-compose -f docker-compose.prod.yml up -d

down: ## Stop all services
	docker-compose down
	docker-compose -f docker-compose.dev.yml down
	docker-compose -f docker-compose.prod.yml down

restart: ## Restart all services
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

logs-backend: ## Show backend logs
	docker-compose logs -f backend

logs-worker: ## Show worker logs
	docker-compose logs -f worker

logs-frontend: ## Show frontend logs
	docker-compose logs -f frontend

clean: ## Remove all containers, volumes, and images
	docker-compose down -v --rmi all
	docker-compose -f docker-compose.dev.yml down -v --rmi all
	docker-compose -f docker-compose.prod.yml down -v --rmi all

test: ## Run tests
	docker-compose exec backend pytest tests/ -v

create-user: ## Create a test user (usage: make create-user USER_ID=tenant1 API_KEY=my-key)
	docker-compose exec backend python scripts/create_user.py $(USER_ID) $(API_KEY)

shell-backend: ## Open shell in backend container
	docker-compose exec backend /bin/bash

shell-db: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U postgres -d job_queue_db

scale-workers: ## Scale workers (usage: make scale-workers COUNT=3)
	docker-compose up -d --scale worker=$(COUNT)

