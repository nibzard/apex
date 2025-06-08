#!/bin/bash
# Test runner script for APEX

set -e

# Set Python path
export PYTHONPATH="./src"

echo "🧪 Running APEX tests..."

# Run pytest with coverage
uv run pytest --cov=apex --cov-report=html --cov-report=term-missing "$@"

echo "✅ Tests completed!"

# Show coverage summary
if [ -f htmlcov/index.html ]; then
    echo "📊 Coverage report available at: htmlcov/index.html"
fi
