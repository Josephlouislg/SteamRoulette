FROM python:3.8.6-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    g++ \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

WORKDIR /app
ADD pyproject.toml /app/
RUN poetry run pip freeze > req.txt && pip install -r req.txt

COPY . .