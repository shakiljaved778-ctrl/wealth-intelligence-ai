.PHONY: help install backend frontend test lint fmt up down

help:
	@echo "install    Install backend + frontend deps"
	@echo "backend    Run FastAPI dev server"
	@echo "frontend   Run Next.js dev server"
	@echo "test       Run backend tests"
	@echo "lint       Lint backend (ruff) + typecheck (mypy)"
	@echo "fmt        Format backend (ruff format)"
	@echo "up/down    docker compose up/down"

install:
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install

backend:
	cd backend && uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

test:
	cd backend && pytest -q

lint:
	cd backend && ruff check app && mypy app

fmt:
	cd backend && ruff format app && ruff check --fix app

up:
	docker compose up --build

down:
	docker compose down
