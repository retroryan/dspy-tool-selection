# Integration Tests for DSPy Agentic Loop

This directory contains comprehensive integration tests for the DSPy agentic loop implementation. These tests use real LLM models and tools to validate the complete workflow.

## Test Structure

### 🧪 Test Modules

1. **`test_full_workflow.py`** - Complete workflow integration tests
   - Simple reminder workflow
   - Complex multi-reminder workflow
   - Response formatting with different styles
   - Conversation history management
   - Error handling scenarios
   - Performance testing

2. **`test_real_model_tools.py`** - Real model and tools integration tests
   - Productivity tools with real LLM
   - Treasure hunt tools with real LLM
   - Ecommerce tools with real LLM
   - Model reasoning quality assessment
   - Tool selection accuracy validation
   - Model configuration validation

3. **`test_framework.py`** - Simple testing framework
   - Custom test runner (no pytest dependency)
   - Basic assertions and test management
   - Result reporting and summary

### 🚀 Running Tests

#### Run All Tests
```bash
# Run the complete test suite
python integration_tests/run_all_tests.py
```

#### Run Individual Test Modules
```bash
# Run full workflow tests only
python integration_tests/test_full_workflow.py

# Run real model and tools tests only
python integration_tests/test_real_model_tools.py
```

## Prerequisites

### 1. Environment Configuration

Ensure your `.env` file is properly configured:

```env
# For Ollama (recommended for integration tests)
DSPY_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:27b

# For Claude (alternative)
#DSPY_PROVIDER=claude
#ANTHROPIC_API_KEY=your-api-key
#CLAUDE_MODEL=claude-3-7-sonnet-20250219
```

### 2. Ollama Setup (if using Ollama)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# Pull the model
ollama pull gemma3:27b
```

### 3. Python Dependencies

```bash
# Install project dependencies
poetry install
```

## Test Coverage

### 🎯 What We Test

#### Full Workflow Tests (6 tests)
- ✅ **Simple Reminder Workflow** - Basic reminder creation
- ✅ **Complex Multi-Reminder Workflow** - Multiple reminders in one request
- ✅ **Response Formatting Workflow** - Different response styles (detailed, concise, technical)
- ✅ **Conversation History Workflow** - Multi-turn conversations with history
- ✅ **Error Handling Workflow** - Graceful handling of impossible requests
- ✅ **Performance Workflow** - Execution time and efficiency

#### Real Model and Tools Tests (6 tests)
- ✅ **Productivity Tools with Real Model** - Testing set_reminder with various scenarios
- ✅ **Treasure Hunt Tools with Real Model** - Testing give_hint and guess_location
- ✅ **Ecommerce Tools with Real Model** - Testing search_products, track_order, return_item
- ✅ **Model Reasoning Quality** - Complex reasoning scenarios
- ✅ **Tool Selection Accuracy** - Correct tool selection for different query types
- ✅ **Model Configuration Validation** - Basic model connectivity and response

### 🔍 Key Validation Points

1. **LLM Integration**
   - Model responds correctly to DSPy signatures
   - Proper handling of structured outputs
   - Reasonable response times

2. **Tool Execution**
   - Correct tool selection based on user queries
   - Successful tool execution with proper arguments
   - Error handling for failed tool calls

3. **Agentic Loop Flow**
   - Proper iteration management
   - Conversation state handling
   - External control via ActivityManager

4. **Response Quality**
   - Meaningful final responses
   - Proper formatting across different styles
   - Confidence scoring and interpretation

## Test Results Interpretation

### Success Criteria

- **All tests pass** - The agentic loop implementation is working correctly
- **High success rate** - Most functionality is working as expected
- **Reasonable performance** - Tests complete within expected time frames

### Common Issues

1. **LLM Connection Failures**
   - Check Ollama service is running
   - Verify model is pulled and available
   - Check API keys for cloud providers

2. **Tool Selection Issues**
   - Review tool descriptions and signatures
   - Check DSPy signature formatting
   - Verify tool registry configuration

3. **Timeout Issues**
   - Increase timeout values for slower models
   - Check model performance and availability
   - Review query complexity

## Adding New Tests

### Test Function Structure

```python
def test_your_scenario(self) -> Dict[str, Any]:
    """Test description."""
    # Setup
    query = "Your test query"
    
    # Execute
    result = self.activity_manager.run_activity(
        user_query=query,
        activity_id="test_id"
    )
    
    # Verify
    self.test_runner.assert_true(result.success, "Test failed")
    
    # Return test details
    return {
        "query": query,
        "success": result.success,
        "details": "additional info"
    }
```

### Adding to Test Suite

1. Add your test method to the appropriate test class
2. Add the test to the `run_all_tests()` method
3. Update this README with test description

## Performance Expectations

### Typical Test Execution Times

- **Individual tests**: 5-15 seconds each
- **Full workflow tests**: 1-2 minutes total
- **Real model tests**: 2-3 minutes total
- **Complete suite**: 3-5 minutes total

### Resource Usage

- **Memory**: ~500MB-1GB for model loading
- **CPU**: Depends on model and hardware
- **Network**: Minimal (local models) or moderate (cloud APIs)

## Troubleshooting

### Common Problems and Solutions

1. **"LLM setup failed"**
   - Verify .env configuration
   - Check Ollama service status
   - Confirm model availability

2. **"Tool execution failed"**
   - Check tool implementations
   - Verify tool registry setup
   - Review tool argument validation

3. **"Test timeout"**
   - Increase timeout values
   - Check model performance
   - Simplify test queries

4. **"Import errors"**
   - Verify Python path setup
   - Check dependency installation
   - Ensure all modules are accessible

### Getting Help

- Review the main project README
- Check DSPy documentation
- Examine test logs for detailed error messages
- Look at successful test runs for comparison

## Integration with CI/CD

These tests can be integrated into CI/CD pipelines:

```bash
# In CI/CD script
export DSPY_PROVIDER=ollama
export OLLAMA_MODEL=gemma3:27b
python integration_tests/run_all_tests.py
```

Note: Cloud-based CI/CD may require different model configuration or mocking for resource constraints.