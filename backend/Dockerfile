FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=2.0.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir poetry==$POETRY_VERSION

COPY pyproject.toml poetry.lock* ./

# Instalamos dependencias
RUN poetry install --only main --no-interaction --no-ansi --no-root

COPY . .

# Permisos para el script de entrada
RUN chmod +x scripts/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/bin/bash", "/app/scripts/entrypoint.sh"]