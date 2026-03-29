-- Script para agregar las nuevas columnas a la tabla users
-- Ejecutar en PostgreSQL: psql -d nombre_db -f update_user_schema.sql

-- Agregar columna avatar_url
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500);

-- Agregar columna notes
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS notes TEXT;

-- Agregar columna last_ip
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS last_ip VARCHAR(45);

-- Agregar columna login_count con valor por defecto 0
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS login_count INTEGER DEFAULT 0;

-- Actualizar registros existentes para que tengan login_count = 0
UPDATE users 
SET login_count = 0 
WHERE login_count IS NULL;

-- Comentarios descriptivos
COMMENT ON COLUMN users.avatar_url IS 'URL de la foto de perfil (Google OAuth)';
COMMENT ON COLUMN users.notes IS 'Notas del administrador sobre el usuario';
COMMENT ON COLUMN users.last_ip IS 'Última dirección IP desde donde accedió';
COMMENT ON COLUMN users.login_count IS 'Total de inicios de sesión realizados';

-- Verificar que las columnas se agregaron correctamente
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('avatar_url', 'notes', 'last_ip', 'login_count')
ORDER BY column_name;
