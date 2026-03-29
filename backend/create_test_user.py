#!/usr/bin/env python3
"""
Script para crear un usuario de prueba en la base de datos.
"""

import sys
import os
import bcrypt
from sqlalchemy.orm import Session

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import engine
from app.models.user import User
from app.types.enums import UserRole, UserStatus

def create_test_user():
    """
    Crea un usuario de prueba para testing.
    """
    # Datos del usuario de prueba
    test_user_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'full_name': 'Usuario de Prueba',
        'password': 'test123',  # Contraseña en texto plano
        'role': UserRole.USER,
        'status': UserStatus.ACTIVE,
        'is_active': True,
        'is_locked': False
    }
    
    # Crear sesión de base de datos
    with Session(engine) as db:
        try:
            # Verificar si el usuario ya existe
            existing_user = db.query(User).filter(
                (User.username == test_user_data['username']) | 
                (User.email == test_user_data['email'])
            ).first()
            
            if existing_user:
                print(f"❌ El usuario '{test_user_data['username']}' ya existe")
                print(f"   Email: {existing_user.email}")
                print(f"   ID: {existing_user.id}")
                return
            
            # Hashear la contraseña
            password_hash = bcrypt.hashpw(
                test_user_data['password'].encode('utf-8'), 
                bcrypt.gensalt()
            ).decode('utf-8')
            
            # Crear nuevo usuario
            new_user = User(
                username=test_user_data['username'],
                email=test_user_data['email'],
                full_name=test_user_data['full_name'],
                password_hash=password_hash,
                role=test_user_data['role'],
                status=test_user_data['status'],
                is_active=test_user_data['is_active'],
                is_locked=test_user_data['is_locked'],
                failed_login_attempts=0,
                origin='test_script'
            )
            
            # Guardar en base de datos
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            print(f"✅ Usuario de prueba creado exitosamente:")
            print(f"   Username: {new_user.username}")
            print(f"   Email: {new_user.email}")
            print(f"   Password: {test_user_data['password']}")
            print(f"   ID: {new_user.id}")
            print(f"   Role: {new_user.role.value}")
            print(f"   Status: {new_user.status.value}")
            
        except Exception as e:
            print(f"❌ Error al crear usuario: {str(e)}")
            db.rollback()
            raise

def list_users():
    """
    Lista todos los usuarios en la base de datos.
    """
    with Session(engine) as db:
        users = db.query(User).all()
        
        if not users:
            print("📭 No hay usuarios en la base de datos")
            return
        
        print(f"👥 Lista de usuarios ({len(users)}):")
        print("-" * 80)
        for user in users:
            print(f"ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Full Name: {user.full_name}")
            print(f"Role: {user.role.value}")
            print(f"Status: {user.status.value}")
            print(f"Active: {user.is_active}")
            print(f"Locked: {user.is_locked}")
            print(f"Failed Attempts: {user.failed_login_attempts}")
            print(f"Created: {user.created_at}")
            print("-" * 80)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Gestionar usuarios de prueba')
    parser.add_argument('--create', action='store_true', help='Crear usuario de prueba')
    parser.add_argument('--list', action='store_true', help='Listar todos los usuarios')
    
    args = parser.parse_args()
    
    if args.create:
        create_test_user()
    elif args.list:
        list_users()
    else:
        print("Uso: python create_test_user.py [--create|--list]")
        print("  --create  : Crear usuario de prueba")
        print("  --list    : Listar todos los usuarios")
