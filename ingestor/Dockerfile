FROM python:3.13-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock* ./
COPY crawler/pyproject.toml crawler/pyproject.toml
COPY server/pyproject.toml server/pyproject.toml
COPY crawler/src crawler/src
COPY server/src server/src

RUN uv sync --all-packages --frozen --no-dev 2>/dev/null || uv sync --all-packages --no-dev

EXPOSE 8000

CMD ["uv", "run", "--package", "server", "fastapi", "run", "server/src/server/main.py", "--host", "0.0.0.0", "--port", "8000"]
