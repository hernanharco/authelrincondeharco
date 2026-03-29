#!/usr/bin/env python3
"""
Script para verificar y actualizar el rol del usuario actual
"""

import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Cargar variables de entorno desde .env
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                value = value.strip()
                if '#' in value:
                    value = value.split('#')[0].strip()
                os.environ[key] = value

def check_and_update_user_role():
    """Verificar y actualizar el rol del usuario hernan.harco@gmail.com"""
    
    # Construir URL de la base de datos
    pg_host = os.getenv("PGHOST", "localhost")
    pg_port = os.getenv("PGPORT", "5432")
    pg_database = os.getenv("PGDATABASE")
    pg_user = os.getenv("PGUSER")
    pg_password = os.getenv("PGPASSWORD")
    pg_schema = os.getenv("PGSCHEMA")
    
    if not all([pg_database, pg_user, pg_password]):
        print("❌ Error: Faltan variables de configuración de PostgreSQL")
        return False
    
    database_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
    if pg_schema:
        database_url += f"?options=-csearch_path%3D{pg_schema}"
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # Verificar usuario actual
            check_query = text("""
                SELECT id, username, email, role, status 
                FROM users 
                WHERE email = :email
            """)
            
            result = connection.execute(check_query, {"email": "hernan.harco@gmail.com"})
            user = result.fetchone()
            
            if not user:
                print("❌ Usuario hernan.harco@gmail.com no encontrado")
                return False
            
            print(f"📋 Usuario encontrado:")
            print(f"   ID: {user.id}")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   Rol actual: {user.role}")
            print(f"   Estado: {user.status}")
            
            # Si no es ADMIN o SUPERADMIN, actualizar a ADMIN
            if user.role not in ['ADMIN', 'SUPERADMIN']:
                print(f"\n🔄 Actualizando rol de {user.role} a ADMIN...")
                
                update_query = text("""
                    UPDATE users 
                    SET role = 'ADMIN', updated_at = CURRENT_TIMESTAMP
                    WHERE email = :email
                """)
                
                connection.execute(update_query, {"email": "hernan.harco@gmail.com"})
                connection.commit()
                
                print("✅ Rol actualizado a ADMIN")
            else:
                print(f"\n✅ El usuario ya tiene rol {user.role} (acceso permitido)")
            
            # Verificar estado
            if user.status != 'ACTIVE':
                print(f"\n🔄 Activando usuario (estado actual: {user.status})...")
                
                update_status_query = text("""
                    UPDATE users 
                    SET status = 'ACTIVE', updated_at = CURRENT_TIMESTAMP
                    WHERE email = :email
                """)
                
                connection.execute(update_status_query, {"email": "hernan.harco@gmail.com"})
                connection.commit()
                
                print("✅ Usuario activado")
            else:
                print(f"\n✅ El usuario ya está ACTIVO")
            
            return True
            
    except SQLAlchemyError as e:
        print(f"❌ Error de base de datos: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Verificando rol del usuario para acceso al dashboard...")
    success = check_and_update_user_role()
    
    if success:
        print("\n🎉 ¡Listo! Ahora puedes acceder al dashboard:")
        print("   1. Inicia sesión en: http://localhost:4321/login")
        print("   2. Ve al dashboard: http://localhost:4321/dashboard")
    else:
        print("\n❌ No se pudo verificar/actualizar el usuario")
        sys.exit(1)
