FROM python:3.11-slim AS base

ENV POETRY_HOME="/opt/poetry" \
    POETRY_VERSION=1.8.3 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/poetry/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl git \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get purge -y --auto-remove curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN poetry install --no-ansi

CMD ["bash", "-lc", "make run"]
