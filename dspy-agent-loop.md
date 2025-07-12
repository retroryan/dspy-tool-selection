# DSPy Manual Agent Loop Implementation

## QUICK TESTING

To run the new agentic loop tests:

```bash
# Run Phase 1-2 tests (Core Models and AgentReasoner)
poetry run python -m pytest tests/test_phase1_models.py tests/test_phase2_reasoner.py -v

# Run Phase 3 tests (ManualAgentLoop)
poetry run python -m pytest tests/test_phase3_manual_agent_loop.py -v

# Run Phase 4 tests (ActivityManager)
poetry run python -m pytest tests/test_phase4_activity_manager.py -v

# Run Phase 5 tests (Registry Integration)
poetry run python -m pytest tests/test_phase5_registry_integration.py -v

# Run Phase 7 tests (Response Formatting and Conversation History)
poetry run python -m pytest tests/test_phase7_response_formatter.py -v

# Run Phase 8 integration tests (Real Model Testing)
poetry run python integration_tests/test_simple_workflow.py

# Run all integration tests
poetry run python integration_tests/run_all_tests.py

# Run all agentic loop tests
poetry run python -m pytest tests/test_phase*.py -v

# Test existing tool selection (still works)
poetry run python -m pytest tests/test_multi_tool_selector.py -v

# Run the multi-tool demo (existing functionality)
poetry run python -m tool_selection.multi_demo
```

**Total Test Coverage**: 
- Phase 1-2: ✅ Core models and reasoning (tested via integration tests)
- Phase 3: ✅ Manual agent loop (11 tests)  
- Phase 4: ✅ Activity manager (14 tests)
- Phase 5: ✅ Registry integration (7 tests)
- Phase 7: ✅ Response formatting and conversation history (28 tests)
- Phase 8: ✅ Integration tests with real models (2 tests, 100% success rate)
- **Total: 62 comprehensive tests for agentic loop implementation**

## Implementation Plan & Checklist

### Phase 1: Core Data Models and Base Structures ✅
- [x] Create `ToolCall` Pydantic model for tool execution requests (*REUSE* from tool_selection)
- [x] Create `ReasoningOutput` model for unified reasoning decisions
- [x] Create `ActionDecision` model for ActivityManager communication  
- [x] Create `ConversationState` model for stateless operation
- [x] Create `ActionType` enum for different action types
- [x] Create `ToolExecutionResult` and `ActivityResult` models
- [x] Test all models with sample data and validation

**Status**: ✅ **COMPLETED** - All core data models implemented and tested
**Location**: `agentic_loop/models.py`
**Testing**: All models pass validation tests with proper field descriptions

### Phase 2: Basic AgentReasoner with Tool Selection ✅
- [x] Implement `AgentReasonerSignature` with all required fields
- [x] Create `AgentReasoner` module with `dspy.ChainOfThought`
- [x] Add tool selection logic with available tools formatting
- [x] Add continuation decision logic with validation
- [x] Add history summarization and tool relevance analysis
- [x] Test with mock tool registry and simple queries
- [x] Validate that tool selection follows type safety patterns
- [x] Test with real LLM integration and validate outputs

**Status**: ✅ **COMPLETED** - Core reasoning module implemented and tested
**Location**: `agentic_loop/agent_reasoner.py`
**Testing**: All reasoning logic passes validation, real LLM integration successful
**Features**: Unified reasoning, tool validation, history management, iteration limits

### Phase 3: ManualAgentLoop with Basic Iteration ✅
- [x] Create `ManualAgentLoop` class inheriting from `dspy.Module`
- [x] Implement `get_next_action()` method for stateless operation
- [x] Add core reasoning integration with `AgentReasoner`
- [x] Add basic error handling for failed tool calls
- [x] Implement helper methods for formatting inputs/outputs
- [x] Test with simple single-iteration scenarios

**Status**: ✅ **COMPLETED** - Manual agent loop with basic iteration implemented
**Location**: `agentic_loop/manual_agent_loop.py`
**Testing**: All tests pass, including mock reasoner integration
**Features**: Stateless operation, external control, helper methods, error handling

### Phase 4: ActivityManager for External Control ✅
- [x] Create `ActivityManager` class with execution control
- [x] Implement `run_activity()` method with iteration loop
- [x] Add sequential tool execution support
- [x] Add activity result creation and formatting
- [x] Test with mock agent and tool registry

**Status**: ✅ **COMPLETED** - Activity manager with external control implemented
**Location**: `agentic_loop/activity_manager.py`
**Testing**: All 14 tests pass, including edge cases and error scenarios
**Features**: External control, sequential execution, iteration management, timeout handling

### Phase 5: Tool Registry Integration ✅
- [x] Move `ToolRegistry` from `tool_selection/` to `shared/registry.py`
- [x] Modify `execute_tool()` to return `ToolExecutionResult` objects
- [x] Update `ActivityManager` to use `ToolRegistry` instead of callback
- [x] Remove `TestMultiToolRegistry` (replaced by unified registry)
- [x] Test registry integration with ActivityManager
- [x] Maintain backward compatibility with `@register_tool` decorator

**Status**: ✅ **COMPLETED** - Unified tool registry working with agentic loop
**Location**: `shared/registry.py`
**Testing**: All 7 tests pass including success/failure scenarios and decorator usage
**Features**: Unified tool execution, error handling, execution timing, decorator registration

### Phase 6: Error Recovery Module 🔮 TODO (Future)
**Note**: Moved to future implementation to keep initial version simple
- [ ] Create `ErrorRecoveryStrategy` Pydantic model
- [ ] Implement `ErrorRecoverySignature` for DSPy
- [ ] Create `ErrorRecoveryModule` with recovery logic
- [ ] Add retry, alternative tool, and graceful degradation strategies
- [ ] Integrate error recovery with `ManualAgentLoop`
- [ ] Test with various error scenarios

### Phase 7: Response Formatting and Conversation History ✅
- [x] Create `ResponseFormatter` module for different output styles
- [x] Implement `ConversationManager` for history management
- [x] Add conversation summarization for long histories
- [x] Add conversation entry models and formatting
- [x] Test with long conversation scenarios

**Status**: ✅ **COMPLETED** - Response formatting and conversation history implementation
**Location**: `agentic_loop/response_formatter.py`
**Testing**: All 28 tests pass including DSPy integration and edge cases
**Features**: DSPy-based formatting, conversation management, history summarization, multiple response styles

### Phase 8: Testing and Validation ✅
- [x] Create comprehensive test suite for all modules
- [x] Add integration tests for full workflow
- [x] Test with real models and tools (Claude & Ollama)
- [x] Validate performance and token usage
- [x] Create simple testing framework without pytest
- [x] Test productivity tools with real workflows

**Status**: ✅ **COMPLETED** - Integration testing with real models successful
**Location**: `integration_tests/` directory
**Testing**: Simple workflow tests pass 100% (2/2 tests)
**Features**: Real model integration, tool selection validation, performance testing

### Phase 9: Documentation and Examples ⏳
- [ ] Create usage examples for each component
- [ ] Add inline code documentation
- [ ] Create README section for agent loop
- [ ] Add troubleshooting guide
- [ ] Create demo script showing full workflow

### Testing Strategy Per Phase
- **Phase 1-2**: Unit tests with mocked dependencies
- **Phase 3-4**: Integration tests with mock tools
- **Phase 5**: Real tool integration tests
- **Phase 6-7**: Error scenario and edge case testing
- **Phase 8**: End-to-end validation with real models
- **Phase 9**: User acceptance testing with examples

### Key Success Criteria
- [ ] Agent successfully selects and executes tools based on user input
- [ ] External ActivityManager has complete control over execution flow
- [ ] Error recovery works for common failure scenarios
- [ ] Conversation history is managed efficiently
- [ ] Implementation follows DSPy best practices and patterns
- [ ] Code is maintainable and well-documented

## Class Organization

**📁 See detailed class organization and reusability analysis in [`agentic_loop/proposal.md`](agentic_loop/proposal.md)**

The implementation will be organized in the `agentic_loop/` directory with clear separation of concerns and maximum reuse of existing `tool_selection/` patterns.

### Key Reusable Components (*REUSE*):
- **BaseTool class and validation patterns** - Perfect foundation for agentic tools
- **ToolRegistry and @register_tool decorator** - Excellent tool management system
- **ToolSet architecture and ToolSetRegistry** - Clean tool organization
- **ToolCall and MultiToolDecision models** - Good for agentic decisions
- **Dynamic signature generation patterns** - Type-safe tool selection

### Simple Tool Set Selection Approach:
- **Static selection at startup** - No dynamic switching during execution
- **Clear separation** - Each tool set is independent (treasure_hunt, productivity, ecommerce, reasoning, control)
- **Simple configuration** - Just specify tool set name when creating ActivityManager

```python
# Example usage
manager = ActivityManager(tool_set_name="treasure_hunt")
result = manager.run_activity("Help me find the treasure!")
```

## Requirements Understanding

Based on the requirements and referenced examples, this proposal outlines a manual agent loop implementation that:

1. **Uses DSPy for LLM interaction only** - NOT using DSPy ReAct module
2. **Manual tool execution control** - Tools are called directly by our code, not by DSPy
3. **Iterative decision making** - After each tool execution, we decide whether to continue
4. **Follows the Strands pattern** - Similar to GEMINI_AGENTIC_LOOP.md and Q_AGENTIC_LOOP.md
5. **External Control via ActivityManager** - The agent loop can be controlled by an external program
6. **Stateless Operation** - Each invocation can receive previous conversation history and tool results
7. **Flexible Execution** - ActivityManager decides when/how to execute tools and continue loops

### Key Architectural Changes for External Control

- **Stateless ManualAgentLoop**: Each call is independent, receiving full context as input
- **ActivityManager Integration**: External program controls loop iteration and tool execution
- **Conversation State Passing**: Previous history and tool results passed as parameters
- **Decoupled Tool Execution**: ActivityManager can execute tools one at a time or async
- **External Loop Counter**: ActivityManager maintains iteration count and termination logic

### Key Differences from DSPy ReAct
- **No automatic tool calling**: We use DSPy to get tool selection decisions, but execute tools ourselves
- **Manual loop control**: We control when to continue or stop the loop
- **Explicit tool result handling**: We format and pass tool results back to the LLM
- **Custom reasoning flow**: We can inject logic between LLM calls and tool executions
- **External orchestration**: ActivityManager controls the overall flow

## High-Level Process Flow with ActivityManager

```
ActivityManager:
1. Creates ManualAgentLoop instance
2. Calls agent.get_next_action(query, history, tool_results)
3. Receives: tool_suggestions[], reasoning, should_continue
4. Executes tools (one by one or async)
5. Evaluates results and decides next step
6. If continuing: Go to step 2 with updated history
7. Else: Generate final response

ManualAgentLoop (per invocation):
1. Receive: query, conversation_history, last_tool_results
2. Analyze context → Suggest tools or final response
3. Return: ActionDecision object with suggestions
```

## Implementation Status

### ✅ **Phase 1 & 2 Complete**: Core Foundation
- **Data Models**: All core Pydantic models implemented and tested (`agentic_loop/models.py`)
- **AgentReasoner**: Unified reasoning module with DSPy ChainOfThought (`agentic_loop/agent_reasoner.py`)
- **Tool Integration**: Reuses existing `ToolCall` from `tool_selection/models.py`
- **Type Safety**: Full validation with proper field descriptions
- **LLM Integration**: Successfully tested with real LLM backend

### 🔄 **Next Steps**: Implementation continues with Phase 3-4 as planned

## Component Architecture Summary

### 1. Core Agent Reasoning Module ✅
**Location**: `agentic_loop/agent_reasoner.py`

**Key Features**:
- Unified reasoning combining tool selection and continuation decisions
- DSPy ChainOfThought for complex reasoning
- History summarization for long conversations
- Tool relevance analysis for better selection
- Output validation with iteration limits
- Type-safe tool validation

### 2. Error Recovery Module ⏳
**Location**: `agentic_loop/error_recovery.py` (Phase 6)

**Planned Features**:
- DSPy-based error analysis and recovery strategies
- Retry with modified parameters
- Alternative tool suggestions
- Graceful degradation strategies

### 3. Response Formatting Module (Optional)
**Location**: `agentic_loop/response_formatter.py` (Phase 7)

**Planned Features**:
- DSPy-based response formatting with style guide support
- Confidence scoring integration
- Summary point extraction from conversation history
- Detailed vs concise output modes
- Integration with ConversationState for context-aware formatting

### 4. Stateless Agent Loop for External Control
**Location**: `agentic_loop/manual_agent_loop.py` (Phase 3)

**Implementation Status**: ⏳ **In Progress**

**Key Features**:
- Stateless design for external control via ActivityManager
- Unified reasoning combining tool selection and continuation decisions
- Error recovery integration with specialized error handling
- Response formatting with confidence scoring
- DSPy-compatible forward method
- Helper methods for conversation history and tool result formatting

**Core Models**:
- `ActionDecision`: Returned by agent for external execution control
- `ConversationState`: Complete state passed between ActivityManager and Agent
- `ActionType`: Enum for different action types (tool_execution, final_response, error_recovery)

**Main Methods**:
- `get_next_action()`: Main entry point for ActivityManager interaction
- `_perform_core_reasoning()`: Uses unified AgentReasoner for tool/continuation decisions
- `_handle_tool_errors()`: Specialized error recovery with alternative tools and retry strategies

### 5. ActivityManager Implementation
**Location**: `agentic_loop/activity_manager.py` (Phase 4)

**Implementation Status**: ⏳ **Planned**

**Key Features**:
- External controller for ManualAgentLoop with full execution control
- Multiple execution modes: sequential, parallel, selective
- Activity lifecycle management with unique IDs
- Tool execution with timing and error handling
- Conversation state management and history tracking
- Custom termination conditions and timeout handling

**Execution Modes**:
- **Sequential**: Execute tools one at a time with full error handling
- **Parallel**: Execute tools concurrently using ThreadPoolExecutor
- **Selective**: Execute tools with custom prioritization and conditional logic

**Main Methods**:
- `run_activity()`: Main execution loop with iteration control
- `_execute_tools()`: Tool execution with mode selection
- `_execute_sequential/parallel/selective()`: Specialized execution strategies
- `_should_terminate()`: Custom termination logic
- `_create_activity_result()`: Activity result formatting

## Key Implementation Details

### 6. Tool Registry Integration
**Location**: `agentic_loop/tool_registry_adapter.py` (Phase 5)

**Implementation Status**: ⏳ **Planned**

**Key Features**:
- Protocol-based compatibility with existing tool registries
- Adapter pattern for current `MultiToolRegistry` integration
- Standardized tool description formatting for LLM consumption
- Error handling for tool lookup and execution
- Type-safe tool name and parameter validation

**Components**:
- `ToolRegistry` Protocol: Interface for tool registry compatibility
- `DSPyToolRegistryAdapter`: Adapter for existing registry systems
- Tool description standardization with parameter metadata
- Error handling and validation for tool lookup operations

### 7. Conversation History Management
**Location**: `agentic_loop/conversation_manager.py` (Phase 7)

**Implementation Status**: ⏳ **Planned**

**Key Features**:
- Conversation history tracking with summarization
- DSPy-based automatic summarization for long conversations
- History compression to manage memory usage
- Formatted history output for LLM consumption
- Error tracking and context preservation

**Components**:
- `ConversationEntry`: Single entry model with iteration metadata
- `ConversationManager`: Main history management with compression
- Automatic summarization using DSPy ChainOfThought
- History formatting for both human and LLM consumption

## Advantages Over DSPy ReAct

1. **Full Control**: Complete control over tool execution timing and parameters
2. **Custom Logic**: Business rules, validation, and transformations between steps
3. **Debugging**: Every step is visible and can be logged/traced
4. **Tool Result Processing**: Filter, transform, or augment results before passing back
5. **State Management**: Maintain custom state, caches, and context
6. **Error Recovery**: Sophisticated error handling with custom recovery strategies
7. **Performance**: Caching, parallel execution, and batch planning
8. **Flexibility**: Easy to add new modules or modify flow
9. **External Orchestration**: ActivityManager provides complete control over execution

## Usage Examples

### Basic Usage Pattern
**Description**: Initialize components and run a simple activity
- Create MultiToolRegistry with tools (search, calculate, weather)
- Initialize ManualAgentLoop with registry adapter and error recovery
- Create ActivityManager with execution mode and iteration limits
- Run activity with user query and process results

### Advanced Control Pattern
**Description**: Custom ActivityManager with specialized termination logic
- Extend ActivityManager with custom termination conditions
- Add pre-validation for tool calls before execution
- Implement confidence-based and error-count-based termination
- Handle critical tool failures with custom recovery strategies

**See**: Implementation examples will be available in `agentic_loop/examples/` directory

## Testing Strategy
**Location**: `tests/test_agentic_loop/` (Phase 8)

**Test Coverage Areas**:
- **Unit Tests**: Individual component testing with mocked dependencies
- **Integration Tests**: Full workflow testing with mock tools
- **Error Handling**: Error recovery and edge case validation
- **Performance Tests**: Token usage and execution timing validation
- **Real Model Tests**: End-to-end validation with actual Ollama models

**Test Categories**:
- Single iteration success scenarios
- Multi-iteration conversation flows
- Error recovery with alternative tools and retry strategies
- Parallel vs sequential tool execution
- Custom termination conditions and timeout handling
- Conversation history management and summarization

**See**: Comprehensive test suite will be available in `tests/test_agentic_loop/` directory

## Dynamic Literals and Type Safety

### Dynamic Signature Generation Analysis

The existing `tool_selection/multi_tool_selector.py` demonstrates an advanced pattern using **Dynamic Signature Generation with Literal types for compile-time safety**:

```python
def create_dynamic_tool_signature(tool_names: tuple[str, ...]) -> Type[dspy.Signature]:
    """Create a signature with dynamic Literal types for compile-time type safety."""
    
    class DynamicToolSelection(BaseModel):
        tool_name: Literal[tool_names]  # Type-safe tool names!
        arguments: Dict[str, Any] = Field(default_factory=dict)
        confidence: float = Field(ge=0, le=1)
```

**Key Benefits:**
- **Compile-time safety**: Tool names are constrained to only valid options
- **Runtime validation**: Pydantic ensures only valid tool names can be selected
- **IDE support**: Auto-completion and type checking for tool names
- **Error prevention**: Impossible to select non-existent tools

### Evaluation for Agentic Loop Implementation

**Decision: NOT implementing dynamic signature generation for the agentic loop**

**Reasoning:**
1. **Simplicity First**: The agentic loop focuses on conversation flow and iteration control, not multi-tool selection
2. **Different Use Case**: The agentic loop uses a single `AgentReasonerSignature` for all reasoning, while multi-tool selection needs different signatures per tool set
3. **Tool Validation Already Exists**: The `AgentReasoner._validate_reasoning_output()` method already validates tool names at runtime
4. **Maintaining Focus**: The agentic loop's core innovation is external control via `ActivityManager`, not advanced type safety

**Current Approach:**
- **String-based tool names**: Simple and flexible for the agentic loop's unified reasoning
- **Runtime validation**: Existing validation in `AgentReasoner` prevents invalid tool usage
- **Clean separation**: Let the multi-tool selector handle advanced type safety for tool selection

**Future Consideration:**
If the agentic loop needs to switch tool sets dynamically, we could adopt dynamic signature generation. However, for the current use case (static tool sets per activity), the complexity isn't justified.

## DSPy Best Practices Alignment

Based on review of DSPy source code and documentation, this implementation follows DSPy best practices:

### ✅ Aligned with DSPy Patterns

1. **Module Structure**: All modules inherit from `dspy.Module` and implement `forward()` method
2. **Signature Design**: Clear input/output fields with descriptive documentation
3. **Type Safety**: Uses `Literal` types for tool selection (via enum integration)
4. **Pydantic Integration**: Structured outputs using Pydantic models
5. **ChainOfThought**: Core reasoning uses `dspy.ChainOfThought` for better LLM reasoning
6. **Manual Control Flow**: Custom logic in `forward()` methods, similar to DSPy's own examples
7. **Synchronous-Only**: Follows DSPy's synchronous patterns (async moved to future-loop.md)

### ✅ Follows DSPy Tool Calling Patterns

1. **Tool Registry**: Dictionary-based tool management similar to DSPy ReAct
2. **Error Handling**: Graceful error capture during tool execution
3. **Trajectory Tracking**: Conversation history similar to ReAct's trajectory pattern
4. **Tool Metadata**: JSON descriptions for LLM consumption

### ✅ Simplified vs DSPy ReAct

| Feature | DSPy ReAct | This Implementation |
|---------|------------|-------------------|
| Tool Execution | Automatic | Manual (Activity Manager) |
| Loop Control | Internal | External |
| Error Recovery | Basic | Configurable |
| State Management | Trajectory Dict | ConversationState |
| Termination | Automatic "finish" | Flexible logic |

### 🎯 Recommendations Applied

1. **Start Simple**: Basic implementation without complex features
2. **Modular Design**: Separate concerns (reasoning, error handling, formatting)
3. **External Control**: ActivityManager provides flexibility beyond DSPy ReAct
4. **Type Safety**: Enum-based tool selection prevents runtime errors
5. **Future Extensibility**: Clean separation allows adding DSPy teleprompters later

## Next Steps

1. **Implementation Priority**:
   - Core loop structure with basic tool selection
   - Basic error handling (simple, not complex recovery)
   - Conversation history management
   - ~~Performance optimizations~~ (moved to future-loop.md)

2. **Integration Points**:
   - Adapt existing MultiToolRegistry
   - Connect to current tool implementations
   - ~~Add monitoring and logging~~ (basic only, complex moved to future-loop.md)

3. **DSPy Best Practices Integration**:
   - Use `dspy.ChainOfThought` for all reasoning modules
   - Follow DSPy's synchronous-only patterns
   - Use Pydantic models for structured outputs (already implemented)
   - Consider teleprompter optimization after basic implementation

4. **Production Readiness**:
   - Comprehensive test suite
   - Performance benchmarks
   - Documentation and examples

