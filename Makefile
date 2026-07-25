# AstraX AI — Makefile
# Common commands for development and deployment

.PHONY: help dev dev-frontend dev-backend install test lint docker clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Development ──────────────────────────────────────────────

dev: ## Start both frontend and backend in development mode
	@echo "Starting AstraX AI..."
	@make dev-backend & make dev-frontend

dev-frontend: ## Start Next.js dev server
	cd frontend && npm run dev

dev-backend: ## Start FastAPI dev server
	cd backend && python -m uvicorn app.main:app --reload --port 8000

install: ## Install all dependencies
	cd frontend && npm install
	cd backend && pip install -r requirements.txt
	cd engine && pip install -e ".[all]"

# ── Testing ──────────────────────────────────────────────────

test: ## Run all tests
	cd engine && python -m pytest tests/ -v
	cd backend && python -m pytest tests/ -v
	cd frontend && npm run lint

test-engine: ## Run engine tests
	cd engine && python -m pytest tests/ -v --cov=astrax_engine

test-backend: ## Run backend tests
	cd backend && python -m pytest tests/ -v --cov=app

lint: ## Run linters
	cd frontend && npm run lint
	cd backend && python -m flake8 app/ --max-line-length=120
	cd engine && python -m flake8 astrax_engine/ --max-line-length=120

# ── Docker ───────────────────────────────────────────────────

docker: ## Build and start Docker containers
	docker compose up --build

docker-down: ## Stop Docker containers
	docker compose down

docker-logs: ## View Docker logs
	docker compose logs -f

# ── Utilities ────────────────────────────────────────────────

clean: ## Clean generated files and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/data frontend/.next
	@echo "Cleaned!"
