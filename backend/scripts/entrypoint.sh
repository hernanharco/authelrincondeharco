#!/bin/bash
set -e

# 1. Esperar a que la DB esté disponible (Local)
echo "🔍 Comprobando conexión con el host '${PGHOST:-localhost}'..."

python -c "
import socket
import time
import os

host = os.getenv('PGHOST', 'localhost')
port = int(os.getenv('PGPORT', 5432))

print(f'⏳ Esperando a que {host}:{port} acepte conexiones...')
start_time = time.time()
while True:
    try:
        # Intentamos abrir un socket
        with socket.create_connection((host, port), timeout=2):
            print('✅ ¡Conexión física establecida!')
            break
    except (socket.timeout, ConnectionRefusedError, socket.gaierror) as e:
        if time.time() - start_time > 30:
            print(f'❌ ERROR: Tiempo de espera agotado conectando a la DB: {e}')
            exit(1)
        time.sleep(2)
"

# 2. Asegurar el Schema (Uso de SQLAlchemy)
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

# Construcción de URL síncrona para DDL inicial
url = f'postgresql+psycopg://{user}:{password}@{host}:{port}/{db}'

try:
    # Conectamos sin schema específico para poder crearlo
    engine = create_engine(url)
    with engine.connect() as conn:
        conn.execution_options(isolation_level='AUTOCOMMIT').execute(text(f'CREATE SCHEMA IF NOT EXISTS {schema}'))
        print(f'✅ Schema \"{schema}\" verificado con éxito.')
except Exception as e:
    print(f'❌ Error crítico al gestionar el schema: {e}')
    exit(1)
"

# 3. Migraciones (Alembic)
# Si no usas Alembic aún, este paso fallará. 
# Si prefieres creación automática por SQLAlchemy: python -m app.db.init_db
echo "📑 Ejecutando migraciones..."
if alembic upgrade head; then
    echo "✅ Migraciones aplicadas."
else
    echo "ℹ️ Saltando migraciones (Alembic no configurado o sin cambios)."
fi

# 4. Lanzar Aplicación con el proceso 1 (Señales de Docker)
echo "🚀 Iniciando servidor FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000