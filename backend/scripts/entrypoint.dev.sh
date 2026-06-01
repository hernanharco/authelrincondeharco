#!/bin/bash
set -e

# ============================================================
# entrypoint.dev.sh — Desarrollo con hot-reload
# ============================================================
# Hace lo mismo que entrypoint.sh pero arranca uvicorn con
# --reload para desarrollo. Las tablas se auto-crean desde
# app/main.py (lifespan handler), no necesita alembic.
# ============================================================

# 1. Esperar a que la DB esté disponible
echo "🔍 Comprobando conexión con el host '${PGHOST:-postgres}'..."
python -c "
import socket, time, os
host = os.getenv('PGHOST', 'postgres')
port = int(os.getenv('PGPORT', 5432))
print(f'⏳ Esperando a que {host}:{port} acepte conexiones...')
start = time.time()
while True:
    try:
        with socket.create_connection((host, port), timeout=2):
            print('✅ ¡Conexión física establecida!')
            break
    except (socket.timeout, ConnectionRefusedError, socket.gaierror) as e:
        if time.time() - start > 30:
            print(f'❌ ERROR: Tiempo de espera agotado: {e}')
            exit(1)
        time.sleep(2)
"

# 2. Asegurar el Schema
echo "🛠️ Asegurando que el esquema '${PGSCHEMA}' exista..."
python -c "
import os
from sqlalchemy import create_engine, text
user = os.getenv('PGUSER')
password = os.getenv('PGPASSWORD')
host = os.getenv('PGHOST')
port = os.getenv('PGPORT', '5432')
db = os.getenv('PGDATABASE')
schema = os.getenv('PGSCHEMA')
url = f'postgresql+psycopg://{user}:{password}@{host}:{port}/{db}'
try:
    engine = create_engine(url)
    with engine.connect() as conn:
        conn.execution_options(isolation_level='AUTOCOMMIT').execute(
            text(f'CREATE SCHEMA IF NOT EXISTS {schema}')
        )
        print(f'✅ Schema \"{schema}\" verificado con éxito.')
except Exception as e:
    print(f'❌ Error al crear schema: {e}')
    exit(1)
"

# 3. Arrancar uvicorn con hot-reload
echo "🚀 Iniciando servidor FastAPI en modo desarrollo (hot-reload)..."
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
