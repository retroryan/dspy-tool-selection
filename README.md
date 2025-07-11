# DSPy Multi-Tool Selection Demo

A comprehensive example demonstrating how to use DSPy with multiple LLM providers (Ollama, Claude, OpenAI, Gemini) for multi-tool selection and execution, featuring type-safe tool registry and dynamic signature generation.

## Primary Goals & Objectives

1. **Maximum Simplicity**: Create the most basic possible synchronous example of using DSPy with multiple LLM providers
2. **Tool Selection Focus**: Demonstrate how to select and call tools based on user intent
3. **Plain Pydantic I/O**: Use simple Pydantic models for structured input and output
4. **Follow Best Practices**: Adhere to DSPy's emphasis on synchronous-only development
5. **No Unnecessary Complexity**: Avoid async patterns, complex abstractions, or heavy frameworks

## Key Principles

- **Synchronous-Only**: All code is synchronous for clarity and simplicity
- **Always use `dspy.ChainOfThought`**: For improved reasoning in tool selection
- **Type Safety**: Pydantic models provide clear data structures
- **Minimal Dependencies**: Just DSPy, Pydantic, and python-dotenv
- **Easy to Understand**: The entire implementation can be grasped in minutes

## Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/) for dependency management
- [Ollama](https://ollama.ai/) installed and running locally
- Gemma2 model pulled in Ollama: `ollama pull gemma3:27b`

## Quick Start

### 1. Install Poetry (if not already installed)

Poetry is a modern dependency management tool for Python. Install it using:

```bash
# On macOS/Linux/WSL
curl -sSL https://install.python-poetry.org | python3 -

# Or using pip
pip install poetry
```

### 2. Clone and set up the project

```bash
# Clone the repository (or navigate to the demo directory)
cd demo-dspy

# Install Python dependencies using Poetry
poetry install

# Copy the example environment file
cp .env.example .env
```

### 3. Start Ollama and pull the model

```bash
# In a separate terminal, start Ollama
ollama serve

# Pull the Gemma3 model (27B parameters)
ollama pull gemma3:27b
```

### 4. Run the demos

#### Multi-Tool Selection Demo

```bash
# Run with default Chain of Thought mode
./run_demo.sh

# Run with debug output (shows DSPy prompts and LLM responses)
./run_demo.sh --debug

# Run with Predict mode (direct prediction, no reasoning steps)
./run_demo.sh --predict

# Run with Predict mode and debug output
./run_demo.sh --predict --debug

# Show help and all available options
./run_demo.sh --help
```

#### Model Comparison

```bash
# Compare specific models
./run_model_comparison.sh --models "gemma3:27b,llama3.1:8b"

# Convert CSV results to markdown summary
./run_model_comparison.sh --create-md --csv model_results.csv -o summary.md

# Show help and all available options
./run_model_comparison.sh --help
```

### 5. Run tests (optional)

The project includes a comprehensive test suite to verify functionality:

```bash
# Run all tests
./tests/run_tests.sh

# Or run tests directly with pytest
poetry run pytest tests/

# Run specific test categories
poetry run pytest tests/test_multi_tool_selector.py   # Multi-tool tests
poetry run pytest tests/test_integration.py        # End-to-end tests

# Run tests with verbose output
poetry run pytest -v tests/
```

**Note**: Tests require a running Ollama instance with an appropriate model.

## DSPy Prediction Modes

This demo supports two DSPy prediction strategies:

### Chain of Thought Mode (Default)
- Uses `dspy.ChainOfThought` for step-by-step reasoning
- The LLM explains its thinking process before selecting a tool
- Generally more accurate for complex decisions
- Provides detailed reasoning in the output

### Predict Mode
- Uses `dspy.Predict` for direct prediction
- Faster and more concise responses
- No intermediate reasoning steps
- May be less accurate for complex tool selection

You can switch between modes using:
- Command line: `./run_demo.sh --predict`
- Environment variable: `DSPY_USE_PREDICT=true`
- Programmatically: `MultiToolSelector(use_predict=True)`

## Using Different LLMs

This demo uses DSPy's unified `dspy.LM` class, which is built on [LiteLLM](https://docs.litellm.ai/), providing support for 100+ LLM providers including local models (Ollama) and cloud providers (Claude, OpenAI, Gemini).

### Quick Provider Switch

The demo supports multiple LLM providers through simple `.env` configuration:

#### Ollama (Local - Default)
```bash
# Current .env configuration works as-is
./run_demo.sh

# Or use the dedicated Ollama config:
cp ollama.env .env
./run_demo.sh
```

#### Claude (Anthropic)
```bash
# Use Claude configuration
cp claude.env .env

# Edit .env and add your API key:
# ANTHROPIC_API_KEY=sk-ant-api03-...

# Run with Claude
./run_demo.sh
```

#### OpenAI
```bash
# Use OpenAI configuration
cp openai.env .env

# Edit .env and add your API key:
# OPENAI_API_KEY=sk-...

# Run with OpenAI
./run_demo.sh
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DSPY_PROVIDER` | LLM provider (`ollama`, `claude`, `openai`, `gemini`) | `ollama` |
| `LLM_TEMPERATURE` | Generation temperature | `0.7` |
| `LLM_MAX_TOKENS` | Maximum tokens to generate | `1024` |
| `DEMO_VERBOSE` | Show connection status | `true` |
| `DSPY_DEBUG` | Enable DSPy debug logging | `false` |

### Provider-Specific Configuration

Each provider supports specific models and settings:

- **Ollama**: `OLLAMA_MODEL`, `OLLAMA_BASE_URL`
- **Claude**: `ANTHROPIC_API_KEY`, `CLAUDE_MODEL`
- **OpenAI**: `OPENAI_API_KEY`, `OPENAI_MODEL`
- **Gemini**: `GOOGLE_API_KEY`, `GEMINI_MODEL`

### Why Use Different Models?

- **Ollama**: Free, private, runs locally, good for development
- **Claude**: Excellent reasoning, great for complex tool selection
- **OpenAI GPT-4**: Strong performance, widely supported
- **Gemini**: Cost-effective, good multimodal capabilities

The same DSPy code works across all providers - just change the configuration!

### Provider-Specific Configuration Files

For easy setup, we provide pre-configured environment files for each provider:

- **`ollama.env`** - Local Ollama models (gemma3:27b, llama3.2, deepseek-r1, etc.)
- **`claude.env`** - Claude models (3.5 Sonnet, 3.7 Sonnet, Sonnet 4)
- **`openai.env`** - OpenAI models (GPT-4o, GPT-4 Turbo, GPT-3.5 Turbo, o1-preview, etc.)

Simply copy the desired configuration to `.env` and add your API keys:

```bash
# Quick setup examples:
cp ollama.env .env    # Use local Ollama
cp claude.env .env    # Use Claude (add ANTHROPIC_API_KEY)
cp openai.env .env    # Use OpenAI (add OPENAI_API_KEY)
```

Each file includes:
- Multiple model options (uncomment to use)
- Recommended settings for each provider
- Helpful comments explaining each model's strengths

## Manual Setup

If you prefer to set up manually:

1. **Install dependencies:**
   ```bash
   poetry install
   ```

2. **Configure Ollama (optional):**
   Edit `.env` to change the model or settings:
   ```env
   OLLAMA_MODEL=gemma3:27b
   OLLAMA_BASE_URL=http://localhost:11434
   ```

3. **Run the demo:**
   ```bash
   poetry run python -m tool_selection.multi_demo
   ```

## What This Demo Does

The demo showcases:
- **Tool Selection**: DSPy analyzes user requests and selects appropriate tools
- **Argument Extraction**: Automatically extracts required arguments from natural language
- **Chain of Thought**: Uses reasoning to explain tool selection decisions

### Example Tools

1. **give_hint**: Provides progressive hints about a treasure location
2. **guess_location**: Validates location guesses

### Example Interactions

- "I need a hint about where the treasure is"
- "I think the treasure is at 300 Lenora in Seattle, WA"

## Project Structure

```
demo-dspy/
├── .env                    # Current LLM configuration
├── ollama.env              # Ollama (local) configuration template
├── claude.env              # Claude configuration template
├── openai.env              # OpenAI configuration template
├── cloud.env.example      # Generic cloud provider template
├── tools/                  # Simple tool implementations
│   ├── give_hint.py
│   └── guess_location.py
├── shared_utils/           # Shared utilities
│   ├── llm_factory.py      # Multi-provider LLM factory
│   ├── metrics.py          # Performance metrics
│   ├── models.py           # Test models
│   └── console.py          # Console formatting
├── tool_selection/         # Multi-tool selection modules
│   ├── multi_demo.py           # Main demo script
│   ├── multi_tool_selector.py  # Multi-tool selection logic
│   ├── tool_registry.py        # Multi-tool registry
│   ├── models.py               # Shared data models
│   ├── test_cases.py           # Test case definitions
│   ├── run_model_comparison.py # Model comparison script
│   └── csv_to_md.py            # CSV to markdown converter
├── setup.sh               # Setup and dependency installation
└── run_demo.sh            # Demo runner with mode selection
```

## Key Concepts

- **Synchronous Only**: Following DSPy best practices for simplicity
- **Pydantic Models**: Type-safe data structures for tools and decisions
- **Chain of Thought**: Always uses `dspy.ChainOfThought` for better reasoning
- **Minimal Dependencies**: Just DSPy, Pydantic, and python-dotenv

## Troubleshooting

- **Ollama not running**: Start Ollama with `ollama serve`
- **Model not found**: Pull the model with `ollama pull gemma2:27b`
- **Poetry not found**: Install Poetry from https://python-poetry.org/

## Next Steps

- Add more tools to the `tools/` directory
- Experiment with different Ollama models
- Extend the tool selection logic for more complex scenarios