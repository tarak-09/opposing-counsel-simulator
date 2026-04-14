SHELL := /bin/bash

API_DIR := apps/api
WEB_DIR := apps/web

.PHONY: api-install api-dev api-test api-lint api-migrate api-seed api-demo web-install web-dev web-lint up down

api-install:
	cd $(API_DIR) && python -m pip install -e ".[dev]"

api-dev:
	cd $(API_DIR) && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

api-test:
	cd $(API_DIR) && pytest

api-lint:
	cd $(API_DIR) && ruff check app tests

api-migrate:
	cd $(API_DIR) && alembic upgrade head

api-seed:
	cd $(API_DIR) && python -m app.utils.seed_data

api-demo:
	cd $(API_DIR) && python -m app.utils.demo_happy_path

web-install:
	npm install

web-dev:
	cd $(WEB_DIR) && npm run dev

web-lint:
	cd $(WEB_DIR) && npm run lint

up:
	docker compose up --build

down:
	docker compose down
