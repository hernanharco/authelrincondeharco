# Backend FastAPI Application

Backend API construido con FastAPI y Neon PostgreSQL que detecta automáticamente el entorno (desarrollo/producción) y ajusta su configuración dinámicamente.

## 🚀 Características Principales

- **FastAPI Framework**: API moderna y asíncrona con documentación automática
- **Neon PostgreSQL**: Base de datos serverless PostgreSQL en la nube
- **Detección Automática de Entorno**: Configuración separada para desarrollo y producción
- **CORS Dinámico**: Orígenes permitidos según el entorno
- **Gestión de Ciclo de Vida**: Startup y shutdown handlers para recursos
- **Health Checks**: Endpoints para verificar estado de la aplicación y conexión a DB
- **Manejo Robusto de Errores**: Captura de fallos de conexión sin detener el servidor

## 📁 Estructura del Proyecto

```
backend/
├── app/
│   ├── __init__.py
│   ├── core/
│   │   └── settings.py      # Configuración y detección de entorno
│   ├── db/
│   │   └── session.py       # Conexión a base de datos Neon
│   └── main.py              # Aplicación FastAPI principal
├── .env                     # Variables de entorno (no versionar)
├── .env.example             # Plantilla de configuración
├── pyproject.toml           # Configuración de Poetry y dependencias
├── poetry.lock              # Lock file de dependencias
└── README.md               # Este archivo
```

## 🛠️ Configuración del Entorno

### Instalar y Configurar Poetry

#### 1. Instalar Poetry
```bash
# Instalar Poetry
curl -sSL https://install.python-poetry.org | python3 -

# O usando pip
pip install poetry
```

#### 2. Configurar el Proyecto
```bash
# Ejecutar script de setup (recomendado)
npm run setup:dev    # Para desarrollo
# o
npm run setup:prod   # Para producción

# O manualmente
poetry install --with dev    # Desarrollo
poetry install --only main   # Producción
```

#### 3. Activar Entorno Virtual
```bash
# Activar el entorno virtual de Poetry
poetry shell

# O ejecutar comandos directamente
poetry run <comando>
```

### 4. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar el archivo .env con tu configuración
nano .env  # o tu editor preferido
```

**Variables importantes a configurar:**

```env
# Environment Configuration
ENVIRONMENT=development

# Database Configuration - Neon PostgreSQL
# Development
DATABASE_URL_DEV=postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/dbname?sslmode=require

# Production
DATABASE_URL_PROD=postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/dbname?sslmode=require

# Application Settings - bash openssl rand -hex 32
DEBUG=true
SECRET_KEY=

# JWT Settings
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# CORS Settings
# Para Desarrollo
CORS_ORIGINS_DEV=http://localhost:3000,http://127.0.0.1:3000
# Para Producción
CORS_ORIGINS_PROD=https://tu-saas-real.com,https://admin.tu-saas.com

# Variables de Google - se toma desde google console - id cliente
GOOGLE_CLIENT_ID=
#secret generado con - se toma desde google console - secreto del cliente
GOOGLE_CLIENT_SECRET=
```

## 🗄️ Configuración de Base de Datos Neon

1. **Crear cuenta en Neon**: Visita [neon.tech](https://neon.tech)
2. **Crear nuevo proyecto**: Selecciona PostgreSQL
3. **Copiar connection string**: Obtén la URL de conexión
4. **Configurar en .env**: Pega la URL en `DATABASE_URL_DEV` o `DATABASE_URL_PROD`

## 🚀 Ejecutar la Aplicación

```bash
# Activar entorno virtual
poetry shell

# Ejecutar en modo desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# O usando npm scripts
npm run dev
```

### Verificar que está funcionando

Abre tu navegador y visita:
- **API Principal**: http://localhost:8000
- **Documentación Swagger**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Info App**: http://localhost:8000/info

## 📡 Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Información básica de la API |
| GET | `/health` | Verifica conexión a la base de datos |
| GET | `/info` | Información detallada del entorno |
| GET | `/docs` | Documentación interactiva Swagger |

## 🔧 Detección Automática de Entorno

La aplicación detecta automáticamente el entorno basado en la variable `ENVIRONMENT`:

### Desarrollo (`ENVIRONMENT=development`)
- Usa `DATABASE_URL_DEV` para la base de datos
- CORS permite orígenes locales (`localhost:3000`, `127.0.0.1:3000`)
- Auto-reload activado
- Debug mode habilitado
- Logs verbosos

### Producción (`ENVIRONMENT=production`)
- Usa `DATABASE_URL_PROD` para la base de datos
- CORS restringido a dominios específicos
- Auto-reload desactivado
- Debug mode desactivado
- Logs optimizados

## 🛡️ Manejo de Errores

La aplicación incluye manejo robusto de errores:

- **Conexión a DB**: Si la URL es incorrecta, muestra advertencia sin detener el servidor
- **Validación de Config**: Verifica que todas las variables requeridas estén presentes
- **Health Checks**: Endpoints para monitorear estado del sistema

## 📦 Dependencias Principales

- `fastapi`: Framework web moderno
- `uvicorn`: Servidor ASGI
- `sqlalchemy`: ORM para base de datos
- `psycopg2-binary`: Driver PostgreSQL
- `pydantic-settings`: Configuración con validación
- `python-dotenv`: Manejo de variables de entorno

## � Comandos Poetry Útiles

### Gestión de Dependencias
```bash
# Instalar dependencias
poetry install

# Instalar solo producción
poetry install --only main

# Agregar nueva dependencia
poetry add fastapi

# Agregar dependencia de desarrollo
poetry add --group dev pytest

# Actualizar dependencias
poetry update

# Exportar a requirements.txt
poetry export -f requirements.txt --output requirements.txt
```

### Ejecución y Testing
```bash
# Ejecutar aplicación
poetry run uvicorn app.main:app --reload

# Ejecutar tests
poetry run pytest

# Ejecutar tests con coverage
poetry run pytest --cov=app --cov-report=html

# Formatear código
poetry run black app/
poetry run isort app/

# Type checking
poetry run mypy app/

# Linting
poetry run flake8 app/
```

### Scripts npm (Disponibles)
```bash
npm run dev              # Iniciar servidor desarrollo
npm run start            # Iniciar servidor producción
npm run test             # Ejecutar tests
npm run test:coverage    # Tests con coverage
npm run lint             # Formatear y lintear
npm run format           # Formatear código
npm run type-check       # Type checking
npm run shell            # Activar entorno Poetry
npm run install          # Instalar dependencias
npm run add              # Agregar dependencia
npm run add:dev          # Agregar dependencia dev
npm run update           # Actualizar dependencias
```

## 🔄 Flujo de Trabajo Típico

1. **Clonar el repositorio**
2. **Instalar Poetry** (si no está instalado)
3. **Ejecutar setup**: `npm run setup:dev`
4. **Configurar .env** con credenciales de Neon
5. **Activar entorno**: `poetry shell` o usar `poetry run`
6. **Ejecutar aplicación**: `npm run dev`
7. **Probar endpoints** en http://localhost:8000/docs

## 🐛 Solución de Problemas Comunes

### Error de conexión a la base de datos
```bash
⚠️  AVISO DE CONFIGURACIÓN DE BASE DE DATOS
No se pudo conectar a la base de datos en: development
```
**Solución**: Verifica que la URL en `.env` sea correcta y que las credenciales de Neon sean válidas.

### Error de importación
```bash
ModuleNotFoundError: No module named 'app'
```
**Solución**: Asegúrate de estar en el directorio raíz del proyecto y que el entorno virtual Poetry esté activado con `poetry shell`.

### Problemas con Poetry
```bash
Poetry no está instalado o no encontrado
```
**Solución**: 
```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
```

### Error de dependencias
```bash
SolverProblemError
```
**Solución**: 
```bash
poetry cache clear --all pypi
poetry install
```

### Puerto en uso
```bash
Address already in use
```
**Solución**: Cambia el puerto o detén el proceso que está usando el puerto 8000.

## 📝 Notas Adicionales

- El archivo `.env` contiene información sensible y no debe ser versionado
- En producción, usa variables de entorno del sistema en lugar del archivo `.env`
- La aplicación maneja gracefully los shutdowns, cerrando conexiones a la base de datos
- Los logs están configurados para mostrar información relevante según el entorno
- **Poetry gestiona automáticamente el entorno virtual**, no es necesario crear venv manualmente
- **poetry.lock** se incluye en version control para reproducibilidad exacta de dependencias
- Usa `poetry export` para generar requirements.txt si es necesario para despliegues