# AuthCore Backend

Backend de autenticación construido con FastAPI y PostgreSQL, diseñado para servir como sistema de autenticación centralizado.

## Stack Tecnológico

- **Python**: ^3.10
- **Framework**: FastAPI ^0.128.0
- **Base de Datos**: PostgreSQL con SQLAlchemy 2.0
- **ORM**: SQLAlchemy ^2.0.23
- **Autenticación**: JWT con python-jose y bcrypt
- **OAuth**: Google OAuth integration
- **Servidor**: Uvicorn/Gunicorn
- **Gestión de Dependencias**: Poetry

## Características

- Autenticación con JWT
- OAuth con Google
- Middleware para Cloudflare/Dokploy
- CORS configurado
- Sistema de migraciones automático
- Health checks
- Documentación API integrada (Swagger/ReDoc)

## Estructura del Proyecto

```
backend/
app/
  api/           # Endpoints de la API
    v1/          # Versión 1 de la API
  core/          # Configuración y utilidades core
  db/            # Configuración de base de datos
  models/        # Modelos de la base de datos
  main.py        # Punto de entrada de la aplicación
tests/           # Tests unitarios y de integración
scripts/         # Scripts de setup y utilidades
nginx/           # Configuración de nginx para producción
```

## Configuración Rápida

### Prerrequisitos

- Python 3.10+
- PostgreSQL
- Poetry (gestor de dependencias)

### Instalación

1. Clonar el repositorio y navegar al directorio `backend`
2. Instalar dependencias:
   ```bash
   make install
   ```
3. Configurar variables de entorno (ver sección de configuración)
4. Iniciar el servidor:
   ```bash
   make dev
   ```

### Variables de Entorno

Crear un archivo `.env` basado en `.env.example`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/dbname

# JWT
SECRET_KEY=tu-secret-key-aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120

# OAuth Google
GOOGLE_CLIENT_ID=tu-google-client-id
GOOGLE_CLIENT_SECRET=tu-google-client-secret

# App
APP_DOMAIN=tu-dominio.com
TITLE_BACKEND=AuthCore Backend
```

## Comandos Disponibles

### Desarrollo
- `make dev` - Iniciar servidor en modo desarrollo con reload
- `make test` - Ejecutar tests
- `make test-cov` - Ejecutar tests con cobertura
- `make lint` - Ejecutar linters (black, isort, flake8)
- `make format` - Formatear código
- `make type-check` - Verificación de tipos con mypy

### Producción
- `make start` - Iniciar servidor en modo producción
- `make install-prod` - Instalar solo dependencias de producción

### Utilidades
- `make shell` - Abrir shell del entorno virtual
- `make add PKG=nombre_paquete` - Añadir dependencia
- `make add-dev PKG=nombre_paquete` - Añadir dependencia de desarrollo
- `make update` - Actualizar dependencias
- `make export` - Exportar requirements.txt

## API Endpoints

La API está disponible en `http://localhost:8000` con los siguientes endpoints:

- `GET /` - Mensaje de bienvenida
- `GET /health` - Health check
- `GET /docs` - Documentación Swagger UI
- `GET /redoc` - Documentación ReDoc
- `GET /openapi.json` - Esquema OpenAPI

Los endpoints de la API v1 están bajo el prefijo `/api/v1/`

## Despliegue

### Docker

```bash
# Construir imagen
docker build -t auth-core-backend .

# Ejecutar con docker-compose
docker-compose up -d
```

### Producción

El backend está configurado para funcionar con:
- **Cloudflare**: Proxy headers middleware habilitado
- **Dokploy**: Compatible con despliegues en VPS
- **Nginx**: Configuración incluida en `nginx/conf.d/`

## Testing

El proyecto incluye tests configurados con pytest:

```bash
# Ejecutar todos los tests
make test

# Ejecutar con cobertura
make test-cov

# Ejecutar tests específicos
poetry run pytest tests/test_auth_endpoints.py -v
```

## Configuración de CORS

El middleware CORS está configurado para permitir:
- Orígenes configurados en `settings.cors_origins`
- Credenciales
- Todos los métodos y headers

## Middleware de Proxy

Importante para producción con Cloudflare/Dokploy:
- `ProxyHeadersMiddleware` habilitado
- Confía en headers `X-Forwarded-*`
- Esencial para cookies `secure=True`

## Contribución

1. Hacer fork del proyecto
2. Crear feature branch
3. Aplicar cambios con `make format` y `make lint`
4. Ejecutar tests con `make test`
5. Crear pull request

## Licencia

Proyecto propiedad de AuthCore Team.
