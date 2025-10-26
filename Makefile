POETRY ?= poetry

.PHONY: install format lint test run api migrate

install:
	$(POETRY) install

format:
	$(POETRY) run scripts/format.sh

lint:
	$(POETRY) run scripts/lint.sh

test:
	$(POETRY) run pytest

run:
	$(POETRY) run python -m triarb.main

api:
	$(POETRY) run uvicorn triarb.api.server:app --host 0.0.0.0 --port $${ADMIN_PORT:-8081}

migrate:
	$(POETRY) run scripts/migrate.sh
