# 🔄 Workflows de Desarrollo - AuthCore

## 📋 Overview

AuthCore incluye workflows automatizados para desarrollo, testing, despliegue y mantenimiento. Estos workflows están diseñados para seguir las mejores prácticas de DevOps y garantizar calidad en todo el ciclo de vida del software.

---

## 🚀 Workflows Disponibles

### 🏗️ /setup - Configuración Inicial
**Descripción**: Configuración completa del entorno de desarrollo
**Uso**: `/setup`

#### Pasos Automatizados
```bash
# 1. Backend setup
cd backend
poetry install
cp .env.example .env
python create_test_user.py --create

# 2. Frontend setup  
cd frontend
pnpm install
cp .env.example .env

# 3. Database setup
docker-compose up -d postgres
# Esperar a que PostgreSQL esté listo
# Crear base de datos y tablas automáticamente

# 4. Verification
poetry run pytest  # Backend tests
pnpm astro check   # Frontend type check
```

#### Variables Requeridas
- `BACKEND_URL=http://localhost:8001`
- `DATABASE_URL=postgresql://...`
- `SECRET_KEY=your-secret-key`
- `GOOGLE_CLIENT_ID=your-google-client-id`
- `GOOGLE_CLIENT_SECRET=your-google-client-secret`

---

### 🧪 /test - Testing Suite Completa
**Descripción**: Ejecutar todos los tests con cobertura y calidad
**Uso**: `/test`

#### Backend Tests
```bash
# Tests unitarios y de integración
pytest --cov=app --cov-report=html --cov-fail-under=80

# Tests específicos
pytest -m auth          # Tests de autenticación
pytest -m users         # Tests de usuarios
pytest -m integration    # Tests de integración
```

#### Frontend Tests
```bash
# Tests de componentes (cuando se implementen)
npm test
npm run test:coverage

# Type checking
pnpm astro check
```

#### Quality Gates
- Backend: 80%+ cobertura requerida
- Frontend: Sin errores TypeScript
- Todos los tests deben pasar
- Sin vulnerabilidades críticas

---

### 🚢 /deploy - Despliegue Producción
**Descripción**: Despliegue automatizado a producción
**Uso**: `/deploy`

#### Pre-deployment Checks
```bash
# 1. Quality assurance
pytest --cov=app
pnpm astro check
black . && isort . && flake8 .

# 2. Security scanning
docker scan backend-bkd-authcore
docker scan frontend-frontend1

# 3. Build optimization
docker build -t backend-bkd-authcore:latest ./backend
docker build -t frontend-frontend1:latest ./frontend
```

#### Deployment Steps
```bash
# 1. Backend deployment
docker stop authcore-backend || true
docker run -d \
  --name authcore-backend \
  --restart unless-stopped \
  -p 8001:8000 \
  --env-file .env.production \
  backend-bkd-authcore:latest

# 2. Frontend deployment (Vercel)
vercel --prod

# 3. Health checks
curl -f http://localhost:8001/health
curl -f https://your-domain.com/
```

---

### 🔧 /dev - Modo Desarrollo
**Descripción**: Iniciar entorno de desarrollo con hot-reload
**Uso**: `/dev`

#### Servicios Concurrentes
```bash
# Terminal 1: Backend
cd backend
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Terminal 2: Frontend
cd frontend  
pnpm dev --port 4321

# Terminal 3: Database (opcional)
docker-compose up postgres

# Terminal 4: Watcher de calidad
pre-commit run --all-files
```

#### Features Activadas
- Hot-reload en backend y frontend
- Auto-restart en cambios de código
- Debug logs activados
- CORS para desarrollo local
- Database migrations automáticas

---

### 📊 /monitor - Monitoreo y Logs
**Descripción**: Monitoreo del estado del sistema
**Uso**: `/monitor`

#### Health Checks
```bash
# Backend health
curl -f http://localhost:8001/health

# Frontend health  
curl -f http://localhost:4321/

# Database connection
docker exec authcore-backend python -c "
import psycopg2
print('✅ Database OK')
"
```

#### Logs en Tiempo Real
```bash
# Backend logs
docker logs -f authcore-backend

# Frontend logs (Vercel)
vercel logs

# System metrics
docker stats
htop
```

#### Performance Metrics
```bash
# Response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8001/api/v1/users/

# Memory usage
docker stats --no-stream authcore-backend

# Database performance
docker exec postgres psql -U postgres -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;
"
```

---

### 🧹 /clean - Limpieza y Mantenimiento
**Descripción**: Limpieza de caches, containers y optimización
**Uso**: `/clean`

#### Docker Cleanup
```bash
# Containers y volumes
docker-compose down -v
docker system prune -a --volumes

# Images no usadas
docker image prune -a

# Build cache
docker builder prune -a
```

#### Development Cleanup
```bash
# Python caches
find . -type d -name __pycache__ -delete
find . -name "*.pyc" -delete

# Node modules y caches
rm -rf node_modules/.cache
pnpm store prune

# Coverage y test artifacts
rm -rf htmlcov/
rm -rf coverage/
```

#### Database Maintenance
```bash
# Vacuum y optimize
docker exec postgres psql -U postgres -d authcore -c "VACUUM ANALYZE;"

# Backup previo al cleanup
docker exec postgres pg_dump -U postgres authcore > backup-$(date +%Y%m%d).sql
```

---

### 🔄 /migrate - Database Migrations
**Descripción**: Migraciones de base de datos y schema updates
**Uso**: `/migrate`

#### Migration Process
```bash
# 1. Backup actual
docker exec postgres pg_dump -U postgres authcore > backup-pre-migration.sql

# 2. Run migrations
cd backend
python -m alembic upgrade head

# 3. Verify data integrity
python scripts/verify_migration.py

# 4. Update application
docker restart authcore-backend
```

#### Rollback Process
```bash
# En caso de error
python -m alembic downgrade -1
docker exec postgres psql -U postgres authcore < backup-pre-migration.sql
```

---

### 📈 /scale - Escalado de Servicios
**Descripción**: Escalado horizontal de servicios
**Uso**: `/scale [service] [instances]`

#### Auto-scaling Commands
```bash
# Escalar backend
./scripts/scale.sh backend 3

# Escalar frontend (load balancer)
./scripts/scale.sh frontend 2

# Escalar database (replicas)
./scripts/scale.sh postgres 2
```

#### Load Balancer Configuration
```bash
# Nginx upstream configuration
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

---

## 🎯 Best Practices

### Antes de Ejecutar Workflows
1. **Leer la documentación** específica del workflow
2. **Verificar prerequisitos** (dependencies, variables)
3. **Hacer backup** de datos críticos
4. **Test en staging** antes de producción

### Durante la Ejecución
1. **Monitorear logs** en tiempo real
2. **Verificar health checks** después de cada paso
3. **Documentar cambios** y decisiones tomadas
4. **Rollback plan** siempre listo

### Después de la Ejecución
1. **Verificar funcionalidad** completa
2. **Limpiar recursos** temporales
3. **Actualizar documentación**
4. **Notificar al equipo** de cambios

---

## 🛠️ Troubleshooting

### Issues Comunes
- **Database connection**: Verificar variables PGHOST, PGPORT
- **Port conflicts**: Liberar puertos 8001, 4321, 5432
- **Permission denied**: Verificar Docker permissions
- **Memory issues**: Aumentar recursos del sistema

### Commands Útiles
```bash
# Debug de containers
docker exec -it authcore-backend bash

# Verificar procesos
ps aux | grep uvicorn
ps aux | grep node

# System resources
df -h
free -h
top
```

---

## 📚 Referencias Adicionales

### Documentación Relacionada
- **Backend**: `.windsurf/backend.md`
- **Frontend**: `.windsurf/frontend.md`
- **Docker**: `.windsurf/docker.md`
- **Testing**: `.windsurf/test.md`
- **Orchestrator**: `.windsurf/orchestrator.md`

### Scripts Automatizados
- `backend/scripts/setup.sh` - Configuración backend
- `frontend/scripts/setup.sh` - Configuración frontend
- `scripts/scale.sh` - Escalado de servicios
- `scripts/backup.sh` - Backup automatizado

---

**AuthCore Workflows** - Automatización profesional para desarrollo eficiente. 🚀🔄
