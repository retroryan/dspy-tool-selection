# TOOLS_LIBRARY.md

## Centralized Tool Registry - Architecture Document

This document serves as an architectural record and implementation guide for the centralized tool registration system in the DSPy tool selection project.

### How to Run Tests

```bash
# Run all tests
poetry run pytest -v

# Run specific test modules
poetry run pytest tests/test_base_tool.py -v      # Base infrastructure tests
poetry run pytest tests/test_registry.py -v       # Registry tests
poetry run pytest tests/test_tool_implementations.py -v  # Tool implementation tests
poetry run pytest tests/test_tool_sets.py -v      # Tool sets tests

# Run with coverage
poetry run pytest --cov=tool_selection tests/

# Run specific test class or method
poetry run pytest tests/test_tool_implementations.py::TestGiveHintTool -v
poetry run pytest tests/test_tool_sets.py::TestIntegration::test_complete_workflow -v
```

### Design Principles

1. **Self-Contained Tools**: Each tool is a complete unit with its schema, implementation, and test cases
2. **Zero Configuration**: Tools register themselves when imported
3. **Tool Sets**: Group related tools into sets that can be loaded together
4. **Enhanced Type Safety**: Leverage Pydantic for automatic validation and type checking
5. **Simplicity**: Keep the system easy to understand and extend with minimal boilerplate

### Architecture Overview

#### Core Components

1. **Base Tool Classes** (`tool_selection/base_tool.py`)
   - `ToolArgument`: Pydantic model for tool arguments with type validation
   - `ToolTestCase`: Model for test cases (renamed from TestCase to avoid pytest conflicts)
   - `ToolMetadata`: Immutable Pydantic model for tool metadata
   - `BaseTool`: Abstract base class using Pydantic for all tools

2. **Tool Registry** (`tool_selection/registry.py`)
   - `ToolRegistry`: Central registry with type-safe operations
   - `register_tool`: Decorator for automatic tool registration
   - Support for tool discovery, filtering, and execution with validation

3. **Tool Sets** (Planned)
   - `ToolSet`: Base class for grouping related tools
   - `ToolSetConfig`: Pydantic model for tool set configuration
   - Dynamic tool loading and test case aggregation

4. **Dynamic Models** (Planned)
   - Dynamic enum generation from registered tools
   - Type-safe tool name references

### Implementation Status

#### ✅ Completed (Steps 1-4)

**Step 1: Base Infrastructure**
- Created `base_tool.py` with Pydantic-based models
- Implemented type validation for tool arguments
- Support for complex types (List[str], Optional fields)
- Automatic validation through `validate_and_execute()`
- Added support for field constraints (min/max values, string length)
- Test coverage: 10/10 tests passing

**Step 2: Registry Implementation**
- Created `registry.py` with type-safe operations
- Implemented tool registration and retrieval
- Category-based filtering
- Automatic validation on tool execution
- Test coverage: 10/10 tests passing

**Step 3: Tool Implementation Examples**
- Converted existing tools to new format
- Created three example tools:
  - `GiveHintTool` (treasure_hunt category)
  - `GuessLocationTool` (treasure_hunt category)
  - `SetReminderTool` (productivity category)
- Implemented argument validation models
- Added field constraints for validation
- Test coverage: 28/28 tests passing

**Step 4: Tool Sets Implementation**
- Created `tool_sets.py` with Pydantic models
- Implemented `ToolSet` base class
- Created `TreasureHuntToolSet` and `ProductivityToolSet`
- Implemented `ToolSetRegistry` for managing tool sets
- Added tool set-specific test cases
- Test coverage: 20/20 tests passing

**Key Features Implemented**
- Pydantic v2 compatibility with ConfigDict
- Field validators and constraints
- Dynamic model creation for argument validation
- Type-safe tool retrieval with generics
- Tool categorization and filtering
- Tool sets for logical grouping
- Comprehensive test coverage (68 tests total)

#### 🔄 In Progress

None - Steps 1-4 completed successfully

#### 📋 Planned (Next Steps)

**Step 5: Integration**
- Update multi_demo.py to use new registry
- Implement dynamic enum generation
- Remove old hardcoded registration

**Step 6: Full Migration**
- Convert all 14 multi-domain tools
- Create comprehensive test suite
- Performance validation

### Technical Decisions

1. **Pydantic Integration**
   - Using Pydantic v2 with updated validators (field_validator)
   - ConfigDict for model configuration (frozen models)
   - Dynamic model creation using create_model() for runtime validation
   - Field constraints passed via ToolArgument.constraints dict

2. **Type Safety Enhancements**
   - Python types instead of strings for arguments
   - Generic type support (List[str], Dict, etc.)
   - Type-safe tool retrieval with TypeVar
   - Automatic type validation before execution

3. **Testing Strategy**
   - Comprehensive unit tests for each component
   - Validation of edge cases and error handling
   - Avoided registry.clear() in tests to prevent side effects
   - Import tools at test module level for consistent state

4. **Tool Organization**
   - Tools organized by category in subdirectories
   - Each tool is self-contained with its validation model
   - Tool sets provide logical grouping with test cases
   - Separation of tool definition from implementation

5. **Constraint Handling**
   - Field constraints stored in ToolArgument model
   - Constraints applied during dynamic model creation
   - Support for Pydantic constraints (ge, le, min_length, max_length)

### Benefits Achieved

1. **Runtime Safety**: All tool arguments validated before execution
2. **Developer Experience**: Full IDE support with type hints
3. **Maintainability**: Clear separation of concerns
4. **Extensibility**: Easy to add new tools without core changes
5. **Error Handling**: Clear validation errors with Pydantic

### Migration Guide

To add a new tool:
1. Create a class inheriting from `BaseTool`
2. Define `metadata` as a class variable with `ToolMetadata`
3. Implement `execute()` and `get_test_cases()` methods
4. Use `@register_tool` decorator for automatic registration
5. Create optional argument validation models for complex types

### Directory Structure

```
tool_selection/
├── base_tool.py                    ✅ Implemented
├── registry.py                     ✅ Implemented
├── tool_sets.py                    ✅ Implemented
├── tools/
│   ├── __init__.py                 ✅ Implemented
│   ├── treasure_hunt/
│   │   ├── __init__.py             ✅ Implemented
│   │   ├── give_hint.py            ✅ Implemented
│   │   └── guess_location.py       ✅ Implemented
│   └── productivity/
│       ├── __init__.py             ✅ Implemented
│       └── set_reminder.py         ✅ Implemented
├── dynamic_models.py               📋 Planned
└── multi_demo.py                   📋 To be updated

tests/
├── test_base_tool.py               ✅ Implemented (10 tests)
├── test_registry.py                ✅ Implemented (10 tests)
├── test_tool_implementations.py    ✅ Implemented (28 tests)
├── test_tool_sets.py               ✅ Implemented (20 tests)
└── test_integration.py             📋 Planned
```

### Validation Results

**Step 1: Base Infrastructure**
- All 10 tests passing
- Pydantic validation working correctly
- Complex type support validated
- Field constraints support added

**Step 2: Registry Implementation**  
- All 10 tests passing
- Tool registration and retrieval working
- Automatic validation on execution confirmed
- Type-safe operations verified

**Step 3: Tool Implementations**
- All 28 tests passing
- Three example tools fully functional
- Argument validation with constraints working
- Category filtering validated

**Step 4: Tool Sets**
- All 20 tests passing
- Tool set loading and registration working
- Test case aggregation functional
- Integration with registry verified

**Total Test Coverage: 68 tests, all passing**

### Next Actions

1. Update multi_demo.py to use the new registry system
2. Implement dynamic enum generation for tool names
3. Migrate remaining tools from the old system
4. Create integration tests for the complete system
5. Performance validation and optimization

---
*Last Updated: Implementation of Steps 1-4 completed with full test coverage (68 tests)*