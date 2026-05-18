.PHONY: dev help setup

help:
	@echo "Available commands:"
	@echo "  make dev    - Start both backend and frontend for local development"
	@echo "  make setup  - Install dependencies for both backend and frontend"

dev:
	./scripts/dev.sh

setup:
	@echo "Installing backend dependencies..."
	cd backend && uv sync
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
