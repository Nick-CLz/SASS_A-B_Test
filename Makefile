.PHONY: help setup dev test lint build

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

setup: ## Install backend + frontend dependencies
	cd backend && uv sync
	cd frontend && pnpm install

dev: ## Print the commands to run the API and the dashboard
	@echo "Run these in two terminals:"
	@echo "  cd backend  && uv run uvicorn app.main:app --reload"
	@echo "  cd frontend && pnpm dev"

test: ## Run backend + frontend tests
	cd backend && uv run pytest
	cd frontend && pnpm test

lint: ## Lint + type-check backend and frontend
	cd backend && uv run ruff check . && uv run mypy app
	cd frontend && pnpm lint

build: ## Build the frontend (and backend image via compose)
	cd frontend && pnpm build
