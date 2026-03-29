#!/usr/bin/env python3
"""
Script para actualizar el esquema de la tabla users con las nuevas columnas.
Ejecutar con: python update_user_schema.py
"""

import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Cargar variables de entorno desde .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            # Ignorar líneas vacías y comentarios
            if not line or line.startswith("#"):
                continue
            # Procesar líneas con formato KEY=VALUE
            if "=" in line:
                # Separar solo el primer '=' para permitir valores con '='
                key, value = line.split("=", 1)
                # Limpiar el valor de espacios y comentarios
                value = value.strip()
                # Si hay un comentario después del valor, quitarlo
                if "#" in value:
                    value = value.split("#")[0].strip()
                os.environ[key] = value

# Agregar el directorio raíz al path para importar configuración
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def update_user_schema():
    """Actualiza la tabla users con las nuevas columnas"""

    # Construir URL de la base de datos desde variables individuales
    pg_host = os.getenv("PGHOST", "localhost")
    pg_port = os.getenv("PGPORT", "5432")
    pg_database = os.getenv("PGDATABASE")
    pg_user = os.getenv("PGUSER")
    pg_password = os.getenv("PGPASSWORD")
    pg_schema = os.getenv("PGSCHEMA")
    pg_sslmode = os.getenv("PGSSLMODE", "disable")

    if not all([pg_database, pg_user, pg_password]):
        print("❌ Error: Faltan variables de configuración de PostgreSQL")
        print("   Requeridas: PGDATABASE, PGUSER, PGPASSWORD")
        print(
            f"   Actuales: PGDATABASE={pg_database}, PGUSER={pg_user}, PGPASSWORD={'***' if pg_password else 'None'}"
        )
        return False

    # Construir URL de conexión
    database_url = (
        f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
    )

    if pg_schema:
        database_url += f"?options=-csearch_path%3D{pg_schema}"

    print(
        f"🔗 Conectando a: postgresql://{pg_user}:***@{pg_host}:{pg_port}/{pg_database}"
    )

    try:
        # Conectar a la base de datos
        engine = create_engine(database_url)
        print("🔗 Conectado a la base de datos")

        # SQL para agregar las nuevas columnas
        sql_statements = [
            # Agregar avatar_url
            """
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500)
            """,
            # Agregar notes
            """
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS notes TEXT
            """,
            # Agregar last_ip
            """
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS last_ip VARCHAR(45)
            """,
            # Agregar login_count
            """
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS login_count INTEGER DEFAULT 0
            """,
            # Actualizar registros existentes
            """
            UPDATE users 
            SET login_count = 0 
            WHERE login_count IS NULL
            """,
            # Agregar comentarios
            """
            COMMENT ON COLUMN users.avatar_url IS 'URL de la foto de perfil (Google OAuth)'
            """,
            """
            COMMENT ON COLUMN users.notes IS 'Notas del administrador sobre el usuario'
            """,
            """
            COMMENT ON COLUMN users.last_ip IS 'Última dirección IP desde donde accedió'
            """,
            """
            COMMENT ON COLUMN users.login_count IS 'Total de inicios de sesión realizados'
            """,
        ]

        # Ejecutar cada statement
        with engine.connect() as connection:
            for i, statement in enumerate(sql_statements, 1):
                try:
                    connection.execute(text(statement))
                    print(f"✅ Statement {i}: Ejecutado correctamente")
                except SQLAlchemyError as e:
                    print(f"⚠️  Statement {i}: {e}")

            connection.commit()

        # Verificar las columnas
        print("\n🔍 Verificando columnas agregadas...")
        verify_query = """
        SELECT column_name, data_type, is_nullable, column_default 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name IN ('avatar_url', 'notes', 'last_ip', 'login_count')
        ORDER BY column_name
        """

        with engine.connect() as connection:
            result = connection.execute(text(verify_query))
            columns = result.fetchall()

            if columns:
                print("\n📋 Columnas encontradas:")
                for col in columns:
                    print(
                        f"  • {col.column_name}: {col.data_type} (nullable: {col.is_nullable})"
                    )
            else:
                print("⚠️  No se encontraron las nuevas columnas")

        print("\n🎉 ¡Actualización completada exitosamente!")
        return True

    except SQLAlchemyError as e:
        print(f"❌ Error de base de datos: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Iniciando actualización del esquema de users...")
    success = update_user_schema()

    if success:
        print("\n✨ Puedes reiniciar el servidor backend ahora")
    else:
        print("\n❌ La actualización falló. Revisa los errores above")
        sys.exit(1)
