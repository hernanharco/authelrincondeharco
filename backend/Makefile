# Makefile para AuthCore Backend

.PHONY: dev start test test-cov lint format type-check shell install install-prod add add-dev update export setup-dev setup-prod

# --- COMANDOS PRINCIPALES ---

# Levantar servidor en modo desarrollo (reload) make dev
dev:
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Levantar servidor en modo producción
start:
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000

# --- GESTIÓN DE DEPENDENCIAS ---

# Instalar todas las dependencias (dev + main)
install:
	poetry install

# Instalar solo dependencias de producción
install-prod:
	poetry install --only main

# Añadir una dependencia (Uso: make add PKG=nombre_paquete)
add:
	poetry add $(PKG)

# Añadir una dependencia de desarrollo (Uso: make add-dev PKG=nombre_paquete)
add-dev:
	poetry add --group dev $(PKG)

# Actualizar todas las dependencias
update:
	poetry update

# --- CALIDAD DE CÓDIGO & TESTS ---

# Ejecutar tests con pytest
test:
	poetry run pytest

# Ejecutar tests con reporte de cobertura HTML
test-cov:
	poetry run pytest --cov=app --cov-report=html

# Ejecutar todos los linters
lint:
	poetry run black app/ && poetry run isort app/ && poetry run flake8 app/

# Formatear código (Black e Isort)
format:
	poetry run black app/ && poetry run isort app/

# Verificar tipos con Mypy
type-check:
	poetry run mypy app/

# --- UTILIDADES ---

# Abrir el shell del entorno virtual
shell:
	poetry shell

# Exportar dependencias a requirements.txt
export:
	poetry export -f requirements.txt --output requirements.txt --without-hashes

# Scripts de inicialización
setup-dev:
	bash poetry-setup.sh development

setup-prod:
	bash poetry-setup.sh production