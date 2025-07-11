# Tests

This directory contains unit and integration tests for the DSPy demo project.

## Test Structure

- `test_multi_tool_selector.py` - Tests for multi-tool selection
- `test_tool_registry.py` - Tests for tool registration and execution
- `test_integration.py` - End-to-end integration tests
- `conftest.py` - Pytest configuration and shared fixtures

## Running Tests

### Quick Run
```bash
# Run all tests
./tests/run_tests.sh

# Or directly with pytest
poetry run pytest tests/
```

### Specific Tests
```bash
# Run a specific test file
poetry run pytest tests/test_multi_tool_selector.py

# Run a specific test
poetry run pytest tests/test_multi_tool_selector.py::test_multiple_tools

# Run with verbose output
poetry run pytest -v tests/
```

### Test Coverage
```bash
# Install coverage tool
poetry add --group dev pytest-cov

# Run with coverage
poetry run pytest --cov=. --cov-report=html tests/
```

## Writing Tests

Tests use pytest framework. Key fixtures available:

- `setup_llm` - Automatically sets up Ollama connection
- `selector` - Creates a multi-tool selector instance
- `tools` - Sample tools for testing
- `registry` - Creates a tool registry
- `system` - Complete system with selector and registry

## Note on LLM Testing

These tests require a running Ollama instance with an appropriate model. Tests use the model specified in `OLLAMA_MODEL` environment variable (defaults to `gemma2:2b` for speed).

Since LLM outputs can vary, tests focus on:
- Correct types and structure
- Presence of required fields
- Reasonable outputs (not exact matches)

## Demo Scripts

The original demo scripts are still available in the project root:
- `tool_selection/multi_demo.py` - Multi-tool scenarios
- `run_model_comparison.py` - Compare different models