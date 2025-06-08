#!/bin/bash
# Development helper script for APEX

set -e

# Set Python path
export PYTHONPATH="./src"

case "$1" in
    "test")
        echo "🧪 Running tests..."
        uv run pytest --no-cov "${@:2}"
        ;;
    "test-cov")
        echo "🧪 Running tests with coverage..."
        uv run pytest --cov=apex --cov-report=html --cov-report=term-missing "${@:2}"
        ;;
    "lint")
        echo "🔍 Running linting..."
        uv run black src tests
        uv run ruff check --fix src tests
        uv run mypy src
        ;;
    "format")
        echo "🎨 Formatting code..."
        uv run black src tests
        uv run ruff format src tests
        ;;
    "cli")
        echo "🚀 Running APEX CLI..."
        uv run apex "${@:2}"
        ;;
    "clean")
        echo "🧹 Cleaning up..."
        rm -rf .coverage htmlcov .pytest_cache
        find . -name "*.pyc" -delete
        find . -name "__pycache__" -delete
        ;;
    *)
        echo "APEX Development Helper"
        echo ""
        echo "Usage: $0 {test|test-cov|lint|format|cli|clean}"
        echo ""
        echo "Commands:"
        echo "  test      - Run tests without coverage"
        echo "  test-cov  - Run tests with coverage"
        echo "  lint      - Run all linting tools"
        echo "  format    - Format code"
        echo "  cli       - Run APEX CLI"
        echo "  clean     - Clean build artifacts"
        ;;
esac