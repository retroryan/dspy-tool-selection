#!/bin/bash
# Run tests for the DSPy demo project

echo "🧪 Running DSPy Demo Tests"
echo "=========================="
echo

# Check if pytest is installed
if ! poetry run python -c "import pytest" 2>/dev/null; then
    echo "📦 Installing pytest..."
    poetry add --group dev pytest
    echo
fi

# Run tests with coverage if available
if poetry run python -c "import pytest_cov" 2>/dev/null; then
    echo "📊 Running tests with coverage..."
    poetry run pytest -v --cov=. --cov-report=term-missing tests/
else
    echo "🧪 Running tests..."
    poetry run pytest -v tests/
fi

echo
echo "✅ Tests complete!"