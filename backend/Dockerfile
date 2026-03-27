# 1. Imagen base
FROM python:3.12-slim

# 2. Variables de entorno para Python y Poetry
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=2.0.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/tmp/poetry_cache'

# 3. Instalación de dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. Directorio de trabajo
WORKDIR /app

# 5. Instalamos Poetry
RUN pip install --no-cache-dir poetry==$POETRY_VERSION

# 6. Copiamos archivos de dependencias
COPY pyproject.toml poetry.lock* ./

# 7. Instalamos dependencias de Python
RUN poetry lock && \
    poetry install --only main --no-root && \
    rm -rf $POETRY_CACHE_DIR

# 8. Copiamos el resto del código
COPY . .

# 9. IMPORTANTE: Aseguramos permisos para los scripts
# Esto garantiza que Docker pueda ejecutar el entrypoint
RUN chmod +x scripts/*.sh

# 10. Exponemos el puerto de FastAPI
EXPOSE 8000

# 11. EL CAMBIO MAESTRO: ENTRYPOINT
# Esto obliga a Docker a ejecutar primero el script que crea el Schema
# y después (gracias al 'exec' al final del script) lanza Uvicorn.
ENTRYPOINT ["/bin/bash", "/app/scripts/entrypoint.sh"]