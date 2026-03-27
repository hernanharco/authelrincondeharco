#!/bin/bash
set -e

# 1. Esperar a que la DB esté disponible
echo "🔍 Comprobando conexión con el host '${PGHOST:-global-db}'..."

python -c "
import socket
import time
import os

host = os.getenv('PGHOST', 'global-db')
port = int(os.getenv('PGPORT', 5432))

print(f'⏳ Esperando a que {host}:{port} acepte conexiones...')
start_time = time.time()
while True:
    try:
        with socket.create_connection((host, port), timeout=1):
            print('✅ ¡Conexión establecida!')
            break
    except (socket.timeout, ConnectionRefusedError, socket.gaierror):
        if time.time() - start_time > 30:
            print('❌ ERROR: Tiempo de espera agotado conectando a la DB.')
            exit(1)
        time.sleep(1)
"

# 2. Asegurar el Schema (Versión Robusta)
echo "🛠️ Asegurando que el esquema '${PGSCHEMA}' exista..."
python -c "
import os
from sqlalchemy import create_engine, text

# Extraemos las piezas del .env
user = os.getenv('PGUSER')
password = os.getenv('PGPASSWORD')
host = os.getenv('PGHOST')
port = os.getenv('PGPORT', '5432')
db = os.getenv('PGDATABASE')
schema = os.getenv('PGSCHEMA')

if not all([user, password, host, db, schema]):
    print(f'❌ Error: Faltan variables de entorno. Schema: {schema}')
    exit(1)

# Construimos la URL de conexión base
url = f'postgresql+psycopg://{user}:{password}@{host}:{port}/{db}?sslmode=disable'

try:
    engine = create_engine(url)
    with engine.connect() as conn:
        # Usamos AUTOCOMMIT para ejecutar comandos de creación de schema (DDL)
        conn.execution_options(isolation_level='AUTOCOMMIT').execute(text(f'CREATE SCHEMA IF NOT EXISTS {schema}'))
        print(f'✅ Schema \"{schema}\" verificado o creado con éxito.')
except Exception as e:
    print(f'❌ Error al crear el schema: {e}')
    exit(1)
"

# 3. Migraciones
echo "📑 Ejecutando migraciones..."
if alembic upgrade head; then
    echo "✅ Migraciones aplicadas con éxito."
else
    echo "⚠️  ADVERTENCIA: Las migraciones fallaron o no hay cambios pendientes."
    echo "Si es la primera vez, asegúrate de que tus modelos estén vinculados a Base."
fi

# 4. Lanzar Aplicación
echo "🚀 Iniciando servidor FastAPI..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000