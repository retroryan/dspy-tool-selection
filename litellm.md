# LiteLLM Multi-Provider Implementation Guide

## Overview

This project now supports multiple LLM providers through DSPy's native LiteLLM integration. You can easily switch between local models (Ollama) and cloud providers (Claude, OpenAI, Gemini) using environment variables.

## Implementation Status ✅

The factory pattern implementation is complete:
- Created `shared_utils/llm_factory.py` with provider-based configuration
- Updated all imports and references throughout the codebase
- Removed the old `ollama_utils.py` file
- Maintained full backward compatibility with Ollama
- Added support for Claude, OpenAI, Gemini, and any LiteLLM-supported provider

## Quick Start

### 1. Using Ollama (Default - No Changes Needed)

```bash
# Existing .env works as-is
poetry run python -m tool_selection.multi_demo
```

### 2. Using Claude

```bash
# Backup your current .env
cp .env .env.ollama

# Use the cloud configuration
cp cloud.env.example .env

# Edit .env and add your API key:
# ANTHROPIC_API_KEY=your-actual-api-key

# Run with Claude
poetry run python -m tool_selection.multi_demo

# To switch back to Ollama:
# cp .env.ollama .env
```

### 3. Using Other Providers

```bash
# Set provider and API key
export DSPY_PROVIDER=openai
export OPENAI_API_KEY=your-openai-key

# Or for Gemini
export DSPY_PROVIDER=gemini
export GOOGLE_API_KEY=your-google-key

# Run the demo
poetry run python -m tool_selection.multi_demo
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DSPY_PROVIDER` | LLM provider to use (`ollama`, `claude`, `openai`, `gemini`) | `ollama` |
| `LLM_TEMPERATURE` | Temperature for generation | `0.7` |
| `LLM_MAX_TOKENS` | Maximum tokens to generate | `1024` |
| `DEMO_VERBOSE` | Show connection status | `true` |
| `DSPY_DEBUG` | Enable DSPy debug logging | `false` |

### Provider-Specific Settings

#### Ollama (Local)
```bash
OLLAMA_MODEL=gemma3:27b
OLLAMA_BASE_URL=http://localhost:11434
```

#### Claude
```bash
ANTHROPIC_API_KEY=your-key
CLAUDE_MODEL=claude-3-opus-20240229
```

#### OpenAI
```bash
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4-turbo-preview
```

#### Gemini
```bash
GOOGLE_API_KEY=your-key
GEMINI_MODEL=gemini-1.5-pro-latest
```

## Cloud Provider Setup

1. **Backup your current .env**:
   ```bash
   cp .env .env.ollama
   ```

2. **Copy and configure cloud template**:
   ```bash
   cp cloud.env.example .env
   ```

3. **Edit .env** and add your API key:
   ```bash
   # For Claude: Add ANTHROPIC_API_KEY=sk-ant-api03-...
   # For OpenAI: Add OPENAI_API_KEY=sk-...
   # For Gemini: Add GOOGLE_API_KEY=...
   ```

4. **Run with cloud provider**:
   ```bash
   poetry run python -m tool_selection.multi_demo
   ```

5. **Switch back to Ollama**:
   ```bash
   cp .env.ollama .env
   ```

## Testing Different Models

### Compare Multiple Models
```bash
# Compare local and cloud models
./run_model_comparison.sh --models "ollama,claude"

# Test specific configurations
DSPY_PROVIDER=ollama poetry run python -m tool_selection.multi_demo
DSPY_PROVIDER=claude poetry run python -m tool_selection.multi_demo
```

### Debug Mode
```bash
# See exact prompts and responses
DSPY_DEBUG=true poetry run python -m tool_selection.multi_demo
```

## Architecture

The implementation uses a factory pattern (`llm_factory.py`) that:
1. Loads environment variables (including `cloud.env` if present)
2. Configures the appropriate LLM based on `DSPY_PROVIDER`
3. Tests the connection before returning
4. Provides helpful error messages for missing API keys

This approach:
- Maintains backward compatibility
- Supports all LiteLLM providers
- Allows easy provider switching
- Keeps configuration centralized
- Provides consistent error handling

## Benefits

1. **Access to Better Models**: Claude and GPT-4 often provide superior results for complex tool selection
2. **Cost Flexibility**: Use free local models for development, premium models for production
3. **No Code Changes**: Switch providers with just environment variables
4. **Provider Agnostic**: Your DSPy code works with any supported LLM

## Troubleshooting

### Connection Failed
- **Ollama**: Ensure Ollama is running and the model is downloaded
- **Claude/OpenAI/Gemini**: Check that your API key is set correctly
- Use `DSPY_DEBUG=true` to see detailed error messages

### Rate Limits
Cloud providers have rate limits. The factory automatically enables LiteLLM's caching to minimize API calls during development.

### Model Not Found
Ensure you're using the correct model names:
- Ollama: Use the exact name from `ollama list`
- Claude: Use full model names like `claude-3-opus-20240229`
- OpenAI: Use names like `gpt-4-turbo-preview`
- Gemini: Use names like `gemini-1.5-pro-latest`