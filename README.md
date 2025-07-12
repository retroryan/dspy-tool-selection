# DSPy Agentic Loop Demo

A comprehensive example demonstrating how to use DSPy with an agentic loop architecture for multi-tool selection and execution across iterations. Features type-safe tool registry, activity management, and support for multiple LLM providers (Ollama, Claude, OpenAI, Gemini).

## Quick Start

### Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/) for dependency management
- [Ollama](https://ollama.ai/) installed and running locally (or API keys for cloud providers)

### Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd dspy-tool-selection

# 2. Install dependencies
poetry install

# 3. Copy environment file
cp .env.example .env

# 4. (Optional) For Ollama: pull the model
ollama pull gemma3:27b
```

### Run the Demo

```bash
# Run with default productivity tools
./run_demo.sh

# Run with specific tool set
./run_demo.sh treasure_hunt

# Run with debug mode to see DSPy prompts
./run_demo.sh --debug

# Available tool sets: treasure_hunt, productivity, ecommerce
```

### Run Tests

```bash
# Run all tests
poetry run pytest

# Run specific test suites
poetry run pytest tests/test_phase3_manual_agent_loop.py
poetry run pytest tests/test_phase4_activity_manager.py
poetry run pytest integration_tests/
```

## What is the Agentic Loop?

The agentic loop is an architecture that allows an AI agent to:
1. **Reason** about user requests and decide which tools to use
2. **Execute** multiple tools in a single iteration or across iterations
3. **Evaluate** results and decide whether to continue or provide a final response
4. **Iterate** up to a maximum number of times to complete complex tasks

Key components:
- **ManualAgentLoop**: Handles reasoning and decision-making using DSPy
- **ActivityManager**: Manages execution flow, iterations, and tool calls
- **ToolRegistry**: Type-safe registry for tool registration and execution

## Detailed Usage

### Running with Different Tool Sets

The demo supports multiple tool sets, each containing related tools:

```bash
# Treasure Hunt Tools (give_hint, guess_location)
./run_demo.sh treasure_hunt

# Productivity Tools (set_reminder)
./run_demo.sh productivity

# E-commerce Tools (search_products, add_to_cart, etc.)
./run_demo.sh ecommerce

# With debug output
./run_demo.sh treasure_hunt --debug
```

### Output and Results

The demo provides:
- Real-time execution progress with reasoning traces
- Performance metrics (precision, recall, F1 score)
- Visual performance bars
- JSON results saved to `test_results/agent_loop_{tool_set}_{timestamp}.json`

### Using Different LLM Providers

The agentic loop supports multiple LLM providers through DSPy's unified interface:

#### Ollama (Local - Default)
```bash
# Already configured in .env.example
./run_demo.sh
```

#### Claude (Anthropic)
```bash
# Copy Claude configuration
cp claude.env .env
# Add your API key to .env: ANTHROPIC_API_KEY=sk-ant-api03-...
./run_demo.sh
```

#### OpenAI
```bash
# Copy OpenAI configuration
cp openai.env .env
# Add your API key to .env: OPENAI_API_KEY=sk-...
./run_demo.sh
```

### Model Comparison

Compare different models on the same tool set:

```bash
# Compare default models (gemma3:27b, llama3.1:8b) on productivity tools
./run_model_comparison.sh

# Compare specific models on treasure hunt
./run_model_comparison.sh treasure_hunt --models "gemma3:27b,llama3.1:8b,llama3.2:3b"

# Test single model on ecommerce
./run_model_comparison.sh ecommerce --models "gemma3:27b"
```

Results are saved to `test_results/model_comparison_{tool_set}_{timestamp}.json`

### Advanced Options

#### Configure Iterations and Timeouts

Edit the ActivityManager initialization in `agent_loop_demo.py`:

```python
activity_manager = ActivityManager(
    agent_loop=agent_loop,
    tool_registry=tool_registry,
    max_iterations=5,      # Increase max iterations
    timeout_seconds=60.0   # Increase timeout
)
```

#### Custom Tool Sets

Create a new tool set by:
1. Implementing tools that inherit from `BaseTool`
2. Creating a `ToolSet` subclass
3. Registering it in `agent_loop_demo.py`

Example:
```python
class MyCustomToolSet(ToolSet):
    NAME = "custom"
    
    def __init__(self):
        super().__init__(
            config=ToolSetConfig(
                name=self.NAME,
                description="My custom tools",
                tool_classes=[MyTool1, MyTool2]
            )
        )
```

## Project Structure

```
dspy-tool-selection/
├── agentic_loop/           # Agentic loop implementation
│   ├── agent_loop_demo.py  # Main demo script
│   ├── agent_reasoner.py   # DSPy reasoning module
│   ├── manual_agent_loop.py # Loop orchestration
│   └── activity_manager.py  # Execution management
├── shared/                 # Shared components
│   ├── models.py           # Core data models
│   ├── registry.py         # Tool registry
│   └── tool_set_registry.py # Tool set management
├── tool_selection/         # Tool sets and definitions
│   ├── tool_sets.py        # Tool set implementations
│   └── base_tool.py        # Base tool class
├── tools/                  # Individual tool implementations
│   ├── treasure_hunt/      # Treasure hunt tools
│   ├── productivity/       # Productivity tools
│   └── ecommerce/          # E-commerce tools
├── tests/                  # Unit tests
├── integration_tests/      # Integration tests
└── test_results/           # Test execution results (gitignored)
```

## Key Concepts

### Agentic Loop Architecture

1. **Stateless Operation**: Each iteration receives full context
2. **External Control**: ActivityManager controls execution flow
3. **Multi-Tool Support**: Can select and execute multiple tools per iteration
4. **Error Recovery**: Built-in error handling and recovery strategies
5. **Iteration Management**: Configurable max iterations with early termination

### Tool Development

Tools must:
- Inherit from `BaseTool`
- Define `NAME` and `MODULE` class attributes
- Implement `execute()` method
- Define `args_model` for input validation
- Return structured results

Example:
```python
class MyTool(BaseTool):
    NAME = "my_tool"
    MODULE = "custom"
    
    class ArgsModel(BaseModel):
        query: str
    
    def execute(self, query: str) -> Dict[str, Any]:
        return {"result": f"Processed: {query}"}
```

## Testing

### Unit Tests
```bash
# Test individual components
poetry run pytest tests/test_phase3_manual_agent_loop.py -v
poetry run pytest tests/test_phase4_activity_manager.py -v
```

### Integration Tests
```bash
# Test full workflows
poetry run pytest integration_tests/test_simple_workflow.py -v
poetry run pytest integration_tests/test_full_workflow.py -v
```

### Running Specific Tests
```bash
# Run tests matching a pattern
poetry run pytest -k "test_multi_tool"

# Run with coverage
poetry run pytest --cov=agentic_loop --cov=shared
```

## Troubleshooting

- **Ollama not running**: Start with `ollama serve`
- **Model not found**: Pull with `ollama pull gemma3:27b`
- **Import errors**: Ensure you're using `poetry run` or activated the virtual environment
- **API key errors**: Check your `.env` file has the correct API keys
- **Timeout errors**: Increase `timeout_seconds` in ActivityManager

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DSPY_PROVIDER` | LLM provider (`ollama`, `claude`, `openai`) | `ollama` |
| `OLLAMA_MODEL` | Ollama model name | `gemma3:27b` |
| `LLM_TEMPERATURE` | Generation temperature | `0.7` |
| `LLM_MAX_TOKENS` | Maximum tokens | `1024` |
| `DSPY_DEBUG` | Show DSPy prompts/responses | `false` |

## Next Steps

- Explore different tool sets and their capabilities
- Create custom tools for your use case
- Experiment with different LLM providers
- Adjust iteration limits and reasoning strategies
- Build complex multi-step workflows