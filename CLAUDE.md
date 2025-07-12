# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Primary Goals & Objectives

**IMPORTANT: Claude must always follow these goals and principles when working on this codebase.**

1. **Maximum Simplicity**: Create the most basic possible synchronous example of using DSPy with agentic loops
2. **Agentic Loop Focus**: Demonstrate how agents can reason, select tools, and iterate to complete tasks
3. **Plain Pydantic I/O**: Use simple Pydantic models for structured input and output
4. **Follow Best Practices**: Adhere to DSPy's emphasis on synchronous-only development
5. **No Unnecessary Complexity**: Avoid async patterns, complex abstractions, or heavy frameworks

## Key Principles

Claude must adhere to these principles:

- **Synchronous-Only**: All code is synchronous for clarity and simplicity
- **Always use `dspy.ChainOfThought`**: For improved reasoning in the agentic loop
- **Type Safety**: Pydantic models provide clear data structures
- **Minimal Dependencies**: Just DSPy, Pydantic, and python-dotenv
- **Easy to Understand**: The entire implementation can be grasped in minutes
- **No Workarounds or Hacks**: Never implement compatibility layers, workarounds, or hacks. Always ask the user to handle edge cases, version conflicts, or compatibility issues directly

**IMPORTANT: If there is a question about something or a request requires a complex hack, always ask the user before implementing. Maintain simplicity over clever solutions.**

**IMPORTANT: Never implement workarounds, compatibility layers, or hacks to handle edge cases or version conflicts. Instead, always inform the user of the issue and ask them how they would like to proceed. This keeps the codebase clean and maintainable.**

## Project Overview

This is a DSPy demo project that demonstrates an agentic loop architecture for multi-tool selection and execution. The project showcases how AI agents can reason about tasks, select appropriate tools, execute them, and iterate based on results - all using DSPy's Chain-of-Thought reasoning with type-safe Pydantic models.

## Key Commands

### Development Commands

```bash
# Install dependencies (using Poetry)
poetry install

# Run the agentic loop demo
poetry run python -m agentic_loop.agent_loop_demo

# Run with specific tool set
poetry run python -m agentic_loop.agent_loop_demo treasure_hunt

# Run tests
poetry run pytest

# Run specific test phases
poetry run pytest tests/test_phase3_manual_agent_loop.py
poetry run pytest tests/test_phase4_activity_manager.py

# Run integration tests
poetry run pytest integration_tests/
```

### Testing & Development

```bash
# Run with debug output to see DSPy prompts and LLM responses
export DSPY_DEBUG=true
poetry run python -m agentic_loop.agent_loop_demo

# Run a simple workflow test
poetry run python -m integration_tests.test_simple_workflow
```

## Architecture Overview

### Core Components

1. **agentic_loop/agent_loop_demo.py**: Main demo script that showcases the agentic loop with different tool sets.

2. **agentic_loop/agent_reasoner.py**: Core DSPy module that performs reasoning about tool selection and task completion:
   - Uses `dspy.ChainOfThought` for step-by-step reasoning
   - Decides which tools to use and whether to continue iterating
   - Returns structured `ReasoningOutput` with tool calls and decisions

3. **agentic_loop/manual_agent_loop.py**: Orchestrates the agentic loop:
   - Stateless operation - receives full context each iteration
   - Converts reasoning output to action decisions
   - Manages conversation state and history

4. **agentic_loop/activity_manager.py**: External control layer for the loop:
   - Manages iterations and timeouts
   - Executes tools based on agent decisions
   - Tracks execution metrics and results
   - Returns complete `ActivityResult` with all execution details

5. **shared/models.py**: Core data models for the agentic loop:
   - `ActionDecision`: What action to take next
   - `ConversationState`: Complete state of the conversation
   - `ToolCall` and `ToolExecutionResult`: Tool execution structures
   - `ActivityResult`: Final result of an activity

6. **shared/registry.py**: Tool registry adapted for agentic loop:
   - Returns `ToolExecutionResult` objects
   - Handles tool execution with error handling
   - Type-safe tool registration

7. **shared/tool_set_registry.py**: Manages collections of related tools:
   - Allows loading specific tool sets (treasure_hunt, productivity, ecommerce)
   - Provides explicit control over available tools

### Key Design Patterns

1. **Agentic Loop Architecture**: 
   - Agent reasons about the task and available tools
   - Executes selected tools
   - Evaluates results and decides whether to continue
   - Iterates until task completion or max iterations

2. **Stateless Operation**: Each iteration receives full context, making the system more robust and easier to debug

3. **External Control**: ActivityManager provides full control over execution flow, allowing for timeouts, error handling, and metrics

4. **Type Safety**: Pydantic models ensure all data structures are validated and type-safe

5. **Multi-Tool Support**: Agents can select and execute multiple tools in a single iteration

### DSPy Concepts Used

- **Chain of Thought**: Core reasoning mechanism for the agent
- **Signatures**: Define input/output contracts for reasoning
- **Pydantic Integration**: Type-safe structured outputs
- **Synchronous Execution**: Following DSPy best practices

## Development Guidelines

When working with the agentic loop:

1. **Adding New Tools**:
   - Create tool class inheriting from `BaseTool`
   - Add to appropriate tool set in `tool_selection/tool_sets.py`
   - Tools are automatically available when their tool set is loaded

2. **Creating Tool Sets**:
   - Subclass `ToolSet` in `tool_selection/tool_sets.py`
   - Define tool classes and test cases
   - Register in `agent_loop_demo.py`

3. **Modifying the Loop**:
   - Keep `ManualAgentLoop` stateless
   - Put execution logic in `ActivityManager`
   - Use `AgentReasoner` for all LLM reasoning

4. **Testing**:
   - Unit tests for individual components
   - Integration tests for full workflows
   - Always test with multiple tool sets

## Configuration

The project uses environment variables configured in `.env`:
- `DSPY_PROVIDER`: LLM provider (ollama, claude, openai)
- `OLLAMA_MODEL`: The Ollama model to use (default: gemma3:27b)
- `OLLAMA_BASE_URL`: Ollama server URL (default: http://localhost:11434)
- `LLM_TEMPERATURE`: Generation temperature (default: 0.7)
- `LLM_MAX_TOKENS`: Maximum tokens (default: 1024)
- `DSPY_DEBUG`: Enable debug output to see prompts and LLM responses

## Prerequisites

- Python 3.10+
- Poetry for dependency management
- Ollama installed and running locally (or API keys for cloud providers)
- Appropriate models pulled (e.g., `ollama pull gemma3:27b`)

## Test Results

Test results are saved to `test_results/` directory with format:
`agent_loop_{tool_set}_{timestamp}.json`

This directory is gitignored to keep the repository clean.