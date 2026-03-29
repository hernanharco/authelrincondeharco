# Actualización del Esquema de Usuarios

## Problema
El error `column users.avatar_url does not exist` ocurre porque agregamos nuevas columnas al modelo SQLAlchemy pero no existen en la base de datos PostgreSQL.

## Solución
Ejecuta uno de los siguientes métodos para actualizar la base de datos:

---

## Método 1: Script Python (Recomendado)

```bash
cd backend
python update_user_schema.py
```

Este script:
- ✅ Se conecta automáticamente usando `DATABASE_URL`
- ✅ Agrega todas las columnas faltantes
- ✅ Actualiza valores por defecto
- ✅ Agrega comentarios descriptivos
- ✅ Verifica la instalación

---

## Método 2: SQL Manual

```bash
cd backend
psql -d tu_base_de_datos -f update_user_schema.sql
```

O ejecuta directamente en PostgreSQL:

```sql
-- Agregar columnas
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500);
ALTER TABLE users ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_ip VARCHAR(45);
ALTER TABLE users ADD COLUMN IF NOT EXISTS login_count INTEGER DEFAULT 0;

-- Actualizar registros existentes
UPDATE users SET login_count = 0 WHERE login_count IS NULL;

-- Agregar comentarios
COMMENT ON COLUMN users.avatar_url IS 'URL de la foto de perfil (Google OAuth)';
COMMENT ON COLUMN users.notes IS 'Notas del administrador sobre el usuario';
COMMENT ON COLUMN users.last_ip IS 'Última dirección IP desde donde accedió';
COMMENT ON COLUMN users.login_count IS 'Total de inicios de sesión realizados';
```

---

## Método 3: Usando Docker

Si usas Docker con PostgreSQL:

```bash
# Copiar el script al contenedor
docker cp update_user_schema.sql postgres_container:/tmp/

# Ejecutar en el contenedor
docker exec postgres_container psql -U postgres -d tu_db -f /tmp/update_user_schema.sql
```

---

## Verificación

Después de ejecutar, verifica que las columnas existan:

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('avatar_url', 'notes', 'last_ip', 'login_count');
```

Deberías ver:
- `avatar_url` | `character varying`
- `notes` | `text`
- `last_ip` | `character varying`
- `login_count` | `integer`

---

## Reiniciar Servidor

Una vez actualizada la base de datos, reinicia el servidor backend:

```bash
cd backend
pnpm dev
```

---

## Notas Importantes

- ⚠️ **Backup**: Haz un backup de tu base de datos antes de ejecutar
- 🔒 **Permisos**: Asegúrate de tener permisos para ALTER TABLE
- 🐳 **Docker**: Si usas Docker, asegúrate que el contenedor esté corriendo
- 🔄 **Rollback**: Los scripts usan `IF NOT EXISTS` para ser seguros

---

## Troubleshooting

### Error: `DATABASE_URL no está configurada`
Asegúrate de tener la variable de entorno en tu `.env`:
```bash
DATABASE_URL=postgresql://usuario:password@localhost:5432/nombre_db
```

### Error: `permission denied for relation users`
Ejecuta con un usuario que tenga permisos de ALTER:
```bash
psql -U postgres -d tu_db
```

### Error: `column already exists`
Los scripts usan `IF NOT EXISTS`, pero si tienes problemas, ejecuta:
```sql
DROP TABLE IF EXISTS users CASCADE;
-- Luego recrea la tabla desde el modelo SQLAlchemy
```
