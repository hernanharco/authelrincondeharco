#!/bin/bash

# Test runner script for the backend
# Usage: bash run-tests.sh [unit|integration|all|coverage]

set -e

TEST_TYPE=${1:-all}

echo "🧪 Running backend tests..."

# Install test dependencies if not already installed
if ! poetry show pytest > /dev/null 2>&1; then
    echo "📦 Installing test dependencies..."
    poetry install --with dev
fi

case $TEST_TYPE in
    "unit")
        echo "🔬 Running unit tests only..."
        poetry run pytest tests/test_models.py tests/test_crud.py tests/test_config.py -v
        ;;
    "integration")
        echo "🔗 Running integration tests only..."
        poetry run pytest tests/test_integration.py tests/test_api.py -v
        ;;
    "all")
        echo "🚀 Running all tests..."
        poetry run pytest tests/ -v
        ;;
    "coverage")
        echo "📊 Running tests with coverage report..."
        poetry run pytest tests/ --cov=app --cov-report=term-missing --cov-report=html
        echo "📈 Coverage report generated in htmlcov/index.html"
        ;;
    "fast")
        echo "⚡ Running fast tests (skip slow)..."
        poetry run pytest tests/ -m "not slow" -v
        ;;
    *)
        echo "❌ Invalid test type. Use: unit, integration, all, coverage, fast"
        exit 1
        ;;
esac

echo "✅ Tests completed!"
