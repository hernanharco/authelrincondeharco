#!/bin/bash

# Poetry Setup Script for AuthCore Backend
# This script installs Poetry and sets up the project

set -e

echo "🚀 Setting up AuthCore Backend with Poetry..."

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "📦 Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    
    # Add Poetry to PATH
    export PATH="$HOME/.local/bin:$PATH"
    
    # Verify installation
    if ! command -v poetry &> /dev/null; then
        echo "❌ Poetry installation failed. Please install manually."
        exit 1
    fi
else
    echo "✅ Poetry is already installed"
fi

# Configure Poetry
echo "⚙️  Configuring Poetry..."
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true

# Install dependencies
echo "📚 Installing dependencies..."
if [ "$1" = "development" ]; then
    echo "🔧 Installing development dependencies..."
    poetry install --with dev
elif [ "$1" = "production" ]; then
    echo "🏭 Installing production dependencies..."
    poetry install --only main
else
    echo "📦 Installing all dependencies..."
    poetry install
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
fi

# Run pre-commit setup if in development
if [ "$1" = "development" ]; then
    echo "🔧 Setting up pre-commit hooks..."
    poetry run pre-commit install
fi

echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Run 'poetry shell' to activate virtual environment"
echo "3. Run 'poetry run uvicorn app.main:app --reload' to start development server"
echo ""
echo "📚 Useful Poetry commands:"
echo "- poetry shell                    # Activate virtual environment"
echo "- poetry run <command>           # Run command in virtual environment"
echo "- poetry add <package>           # Add new dependency"
echo "- poetry add --group dev <pkg>   # Add dev dependency"
echo "- poetry update                  # Update dependencies"
echo "- poetry export                  # Export requirements.txt"
