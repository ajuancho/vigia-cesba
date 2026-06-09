.PHONY: help up down api web worker beat test fmt migrate migrate-sql revision ingest-infoleg

VENV ?= .venv
PY := $(VENV)/Scripts/python
ALEMBIC := $(VENV)/Scripts/alembic

help:
	@echo "vigia dev targets:"
	@echo "  make up              - start db + redis (Docker Desktop required)"
	@echo "  make down            - stop everything"
	@echo "  make api             - run FastAPI in reload mode"
	@echo "  make web             - run Next.js dev server"
	@echo "  make worker          - run celery worker locally"
	@echo "  make beat            - run celery beat schedule locally"
	@echo "  make migrate         - apply alembic migrations against \$$DATABASE_URL"
	@echo "  make migrate-sql     - print SQL Alembic would run (no DB needed)"
	@echo "  make revision m=\"msg\" - generate a new alembic revision"
	@echo "  make ingest-infoleg  - run InfoLEG ingestion task once (needs Postgres)"
	@echo "  make test            - run pytest"
	@echo "  make fmt             - run ruff format + check"

up:
	docker compose up -d db redis

down:
	docker compose down

api:
	$(PY) -m uvicorn vigia_api.main:app --reload --port 8000

web:
	cd apps/web && pnpm dev

worker:
	$(VENV)/Scripts/celery -A vigia_workers worker --loglevel=info --concurrency=2

beat:
	$(VENV)/Scripts/celery -A vigia_workers beat --loglevel=info

migrate:
	$(ALEMBIC) -c db/alembic.ini upgrade head

migrate-sql:
	$(ALEMBIC) -c db/alembic.ini upgrade head --sql

revision:
	$(ALEMBIC) -c db/alembic.ini revision -m "$(m)"

ingest-infoleg:
	$(PY) -c "from vigia_workers.tasks import ingest_infoleg as t; print(t())"

test:
	$(PY) -m pytest packages/connectors/tests apps/api/tests

fmt:
	$(PY) -m ruff check --fix .
	$(PY) -m ruff format .
