# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Primary Goals & Objectives

**IMPORTANT: Claude must always follow these goals and principles when working on this codebase.**

1. **Maximum Simplicity**: Create the most basic possible synchronous example of using DSPy with Ollama
2. **Tool Selection Focus**: Demonstrate how to select and call tools based on user intent
3. **Plain Pydantic I/O**: Use simple Pydantic models for structured input and output
4. **Follow Best Practices**: Adhere to DSPy's emphasis on synchronous-only development
5. **No Unnecessary Complexity**: Avoid async patterns, complex abstractions, or heavy frameworks

## Key Principles

Claude must adhere to these principles:

- **Synchronous-Only**: All code is synchronous for clarity and simplicity
- **Always use `dspy.ChainOfThought`**: For improved reasoning in tool selection
- **Type Safety**: Pydantic models provide clear data structures
- **Minimal Dependencies**: Just DSPy, Pydantic, and python-dotenv
- **Easy to Understand**: The entire implementation can be grasped in minutes
- **No Workarounds or Hacks**: Never implement compatibility layers, workarounds, or hacks. Always ask the user to handle edge cases, version conflicts, or compatibility issues directly

**IMPORTANT: If there is a question about something or a request requires a complex hack, always ask the user before implementing. Maintain simplicity over clever solutions.**

**IMPORTANT: Never implement workarounds, compatibility layers, or hacks to handle edge cases or version conflicts. Instead, always inform the user of the issue and ask them how they would like to proceed. This keeps the codebase clean and maintainable.**

## Project Overview

This is a DSPy demo project that demonstrates multi-tool selection and execution using Language Models (LLMs) with Ollama. The project showcases type-safe multi-tool selection using Pydantic models, dynamic signature generation, and DSPy's Chain-of-Thought reasoning.

## Key Commands

### Development Commands

```bash
# Install dependencies (using Poetry)
poetry install

# Run the multi-tool demo
poetry run python -m tool_selection.multi_demo

# Run model comparison
./run_model_comparison.sh --models "gemma3:27b,llama3.1:8b"

# Run with debug output to see DSPy prompts and LLM responses
./run_demo.sh --debug
# or set DSPY_DEBUG=true in .env

# Quick start (checks dependencies and runs demo)
./run_demo.sh
```

### Testing & Development

```bash
# Run a single example
poetry run python -m tool_selection.multi_demo

# Enable debug mode to inspect DSPy prompts
export DSPY_DEBUG=true
poetry run python -m tool_selection.multi_demo
```

## Architecture Overview

### Core Components

1. **tool_selection/multi_demo.py**: Main entry point that demonstrates multi-tool selection with example user requests.

2. **tool_selection/multi_tool_selector.py**: Contains the DSPy module for multi-tool selection using type-safe Pydantic models. Key concepts:
   - Dynamic signature generation with Literal types for compile-time safety
   - `MultiToolSelector` module using `dspy.ChainOfThought` for reasoning
   - Support for selecting multiple tools in a single request

3. **tool_selection/tool_registry.py**: Multi-tool registry for managing and executing tools
   - `MultiToolRegistry` pattern for clean tool execution
   - Type-safe tool registration and execution

4. **tool_selection/models.py**: Shared data models
   - `MultiToolName` enum for type-safe tool identifiers
   - Pydantic models for tool definitions and decisions

5. **shared_utils/ollama_utils.py**: Configuration utilities for setting up the Ollama LLM backend

6. **tool_selection/test_cases.py**: Test case definitions for multi-tool selection scenarios

7. **tools/**: Directory containing tool implementations
   - `give_hint.py`: Provides progressive hints about a treasure location
   - `guess_location.py`: Validates location guesses

8. **shared_utils/**: Shared utilities across the project
   - `ollama_utils.py`: Ollama configuration and setup
   - `metrics.py`: Performance metrics calculation
   - `models.py`: Test result and comparison models
   - `console.py`: Console output formatting

### Key Design Patterns

1. **Type Safety**: Uses Python enums and Literal types to ensure tool names are type-safe and prevent runtime errors from typos

2. **Dynamic Signatures**: Creates DSPy signatures dynamically based on available tools, allowing the system to adapt as new tools are added

3. **Tool Registry**: Instead of if/elif chains, uses a registry pattern for cleaner tool execution and better maintainability

4. **Synchronous-Only**: Following DSPy best practices, all code is synchronous for clarity and simplicity

### DSPy Concepts Used

- **Signatures**: Define input/output contracts for the LLM
- **Chain of Thought**: Improves reasoning by having the LLM think step-by-step
- **Pydantic Integration**: Ensures type safety and automatic validation
- **Dynamic Literal Types**: Constrains tool selection to valid options

## Development Guidelines

When adding new tools:

1. Add the tool name to the `MultiToolName` enum in `tool_selection/models.py`
2. Create the tool implementation in `tools/` directory
3. Register the tool in `tool_selection/multi_demo.py` using the registry pattern
4. Update the tool definitions in the registry

## Configuration

The project uses environment variables configured in `.env`:
- `OLLAMA_MODEL`: The Ollama model to use (default: gemma3:27b)
- `OLLAMA_BASE_URL`: Ollama server URL (default: http://localhost:11434)
- `DSPY_DEBUG`: Enable debug output to see prompts and LLM responses

## Prerequisites

- Python 3.10+
- Poetry for dependency management
- Ollama installed and running locally
- Gemma3 model pulled: `ollama pull gemma3:27b`