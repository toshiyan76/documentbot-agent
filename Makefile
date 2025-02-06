# Help message
.PHONY: help
help:
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  make init        - Initialize project (build containers and install dependencies)"
	@echo "  make dev         - Start development environment"
	@echo "  make start       - Start production environment"
	@echo "  make stop        - Stop all containers"
	@echo "  make down        - Stop and remove all containers"
	@echo ""
	@echo "Frontend:"
	@echo "  make front-init  - Initialize frontend container"
	@echo "  make front-dev   - Start frontend development server"
	@echo "  make front-build - Build frontend for production"
	@echo ""
	@echo "Backend:"
	@echo "  make back-init   - Initialize backend container"
	@echo "  make back-dev    - Start backend development server"
	@echo "  make back-test   - Run backend tests"
	@echo ""
	@echo "Infrastructure:"
	@echo "  make tf-init     - Initialize Terraform"
	@echo "  make tf-plan     - Show Terraform plan"
	@echo "  make tf-apply    - Apply Terraform changes"

# Default target
.DEFAULT_GOAL := help

# Docker compose commands
.PHONY: build up stop down
build:
	docker compose build --no-cache

up:
	docker compose up -d

stop:
	docker compose stop

down:
	docker compose down

# Development commands
.PHONY: init dev start
init:
	@make build
	@make front-install
	@make back-install

dev:
	@make up
	@make front-install
	@make front-dev

start:
	@make build
	@make up

# Frontend commands
.PHONY: front-init front-dev front-build front-install
front-init:
	docker compose build --no-cache frontend
	@make front-install

 front-dev:
	docker compose exec frontend npm run dev

front-build:
	docker compose run --rm frontend npm run build

front-install:
	docker compose run --rm frontend npm install

# Backend commands
.PHONY: back-init back-dev back-test back-install
back-init:
	docker compose build --no-cache backend
	@make back-install
	@make back-up

back-dev:
	docker compose exec backend python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload

back-test:
	docker compose run --rm backend pytest

back-install:
	docker compose run --rm backend pip install -r requirements.txt

# Terraform commands
.PHONY: tf-init tf-plan tf-apply
tf-init:
	cd terraform/init && terraform init

tf-plan:
	cd terraform/application && terraform plan

tf-apply:
	cd terraform/application && terraform apply

# Removed duplicate back-init target

.PHONY: back-restart
back-restart:
	@make back-down
	@make back-up

.PHONY: back-build
back-build:
	docker compose build --no-cache backend

.PHONY: back-build-with-cache
back-build-with-cache:
	docker compose build backend

.PHONY: go-mod-tidy
go-mod-tidy:
	docker compose run --rm backend go mod tidy

.PHONY: back-up
back-up:
	docker compose up -d backend

.PHONY: back-stop
back-stop:
	docker compose stop backend

.PHONY: back-down
back-down:
	docker compose down backend

include .env
NETWORK_NAME=network-prod

.PHONY: prod-init-start
prod-init-start:
	@make prod-init
	@make prod-start

.PHONY: prod-init
prod-init:
	@make prod-network-create
	@make prod-back-build
	@make prod-front-build

.PHONY: prod-init-with-cache
prod-init-with-cache:
	@make prod-network-create
	@make prod-back-build-with-cache
	@make prod-front-build-with-cache

.PHONY: prod-start
prod-start:
	@make prod-back-run
	@make prod-front-run

.PHONY: prod-stop
prod-stop:
	@make prod-back-stop
	@make prod-front-stop

.PHONY: prod-down
prod-down:
	@make prod-back-stop
	@make prod-front-stop
	@make prod-back-down
	@make prod-front-down
	@make prod-network-remove

.PHONY: prod-back-build
prod-back-build:
	docker build --no-cache -t backend-prod --build-arg API_PORT=${BACKEND_PORT} ./backend
.PHONY: prod-back-build-with-cache
prod-back-build-with-cache:
	docker build -t backend-prod --build-arg API_PORT=${BACKEND_PORT} ./backend
.PHONY: prod-back-run
prod-back-run:
	docker run --rm --name backend-prod -d -p ${BACKEND_PORT}:8080 --network $(NETWORK_NAME) backend-prod
.PHONY: prod-back-stop
prod-back-stop:
	docker stop backend-prod
.PHONY: prod-back-down
prod-back-down:
	docker rmi -f backend-prod

.PHONY: prod-front-build
prod-front-build:
	docker build --no-cache -t frontend-prod --build-arg NEXT_PUBLIC_API_URL=http://backend-prod:8081 ./frontend
.PHONY: prod-front-build-with-cache
prod-front-build-with-cache:
	docker build -t frontend-prod --build-arg NEXT_PUBLIC_API_URL=http://backend-prod:8081 ./frontend
.PHONY: prod-front-run
prod-front-run:
	docker run --rm --init --name frontend-prod -d -p ${FRONTEND_PORT}:3000 --network $(NETWORK_NAME) frontend-prod
.PHONY: prod-front-stop
prod-front-stop:
	docker stop frontend-prod
.PHONY: prod-front-down
prod-front-down:
	docker rmi -f frontend-prod 


.PHONY: prod-network-create
prod-network-create:
	@if [ -z "$$(docker network ls --filter name=^$(NETWORK_NAME)$$ --format='{{ .Name }}')" ]; then \
		docker network create --driver=bridge $(NETWORK_NAME); \
		echo "$(NETWORK_NAME) created"; \
	else \
		echo "$(NETWORK_NAME) already exists"; \
	fi
.PHONY: prod-network-remove
prod-network-remove:
	docker network rm $(NETWORK_NAME)

.PHONY: ps
ps:
	docker compose ps

.PHONY: python-install
python-install:
	docker compose -f compose-init.yaml run --rm backend pip install -r requirements.txt

.PHONY: clean
clean:
	docker compose down --rmi all --volumes --remove-orphans