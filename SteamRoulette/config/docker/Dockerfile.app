FROM python:3.8.6-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    g++ \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

WORKDIR /app
ADD /poetry.lock pyproject.toml /app/
RUN poetry env use 3.8 && poetry install

COPY . .