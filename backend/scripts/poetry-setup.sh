#!/bin/bash

# Poetry setup script for auth-core-backend
# Usage: bash poetry-setup.sh [development|production]

set -e

ENVIRONMENT=${1:-development}

echo "🚀 Setting up auth-core-backend in $ENVIRONMENT mode..."

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install Poetry first:"
    echo "   curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "🐍 Python version: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" < "3.12" ]]; then
    echo "⚠️  Warning: Python 3.12+ is recommended. Current version: $PYTHON_VERSION"
fi

# Install dependencies
echo "📦 Installing dependencies..."
if [ "$ENVIRONMENT" = "production" ]; then
    poetry install --only main
else
    poetry install
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env template..."
    cat > .env << EOF
# PostgreSQL Local Configuration
PGHOST=localhost
PGPORT=5432
PGDATABASE=neondb
PGUSER=neondb_owner
PGPASSWORD=your-password
PGSSLMODE=disable
PGCHANNELBINDING=disable

# Database URL (auto-generated)
DATABASE_URL=postgresql+psycopg://\${PGUSER}:\${PGPASSWORD}@\${PGHOST}:\${PGPORT}/\${PGDATABASE}

# Application Settings
DEBUG=true
SECRET_KEY=your-secret-key-here
CLOUDINARY_CLOUD_NAME=your-cloudinary-cloud-name
CLOUDINARY_API_KEY=your-cloudinary-api-key
CLOUDINARY_API_SECRET=your-cloudinary-api-secret
FRONTEND_URL=http://localhost:4321
EOF
    echo "✅ .env template created. Please update with your local PostgreSQL credentials."
else
    echo "✅ .env file already exists."
fi

# Run initial setup
echo "🔧 Running initial setup..."
poetry run python -c "
import sys
sys.path.insert(0, '.')
try:
    from app.core.config import settings
    print('✅ Configuration loaded successfully')
    print(f'Database URL configured: {bool(settings.database_url)}')
except ImportError as e:
    print(f'⚠️  Import error (expected during first setup): {e}')
except Exception as e:
    print(f'❌ Configuration error: {e}')
"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your local PostgreSQL credentials"
echo "2. Run 'poetry shell' to activate virtual environment"
echo "3. Run 'poetry run uvicorn app.main:app --reload' to start the development server"
echo ""
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Production commands:"
    echo "- poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000: Start production server"
    echo "- docker build -t backend . : Build Docker image"
else
    echo "Development commands:"
    echo "- poetry run uvicorn app.main:app --reload: Start development server"
    echo "- poetry run pytest: Run tests"
    echo "- poetry run black . : Format code"
    echo "- poetry run isort . : Sort imports"
fi
