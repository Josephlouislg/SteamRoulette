FROM python:3.8.6-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    g++ \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

WORKDIR /app
ADD pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

COPY . .