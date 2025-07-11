# Proposal: Consolidate to a Single Tool Model

## Overview

Currently, the system has multiple redundant representations of tools:
1. `ToolMetadata` - metadata about a tool
2. `BaseTool` - the actual tool implementation
3. `MultiTool` - representation for the selector
4. `MultiToolName` enum - hardcoded list of tool names
5. Tool schema dictionaries from `to_schema()`

This creates unnecessary complexity and conversion layers. This proposal outlines how to consolidate to a single, unified tool model that leverages Pydantic for type safety while maintaining flexibility.

## Core Principles

1. **Single Tool Model**: One `BaseTool` class that contains both definition and implementation
2. **Type Safety via Pydantic**: Leverage Pydantic models for argument validation
3. **No Magic Strings**: Tool names defined as static constants on the tool class
4. **Registry as Source of Truth**: Available tools determined by what's registered, not hardcoded lists

## Proposed Architecture

```
ToolSet (defines which tools to load via class references)
    ↓
Tool Classes (self-register via @register_tool, contain all metadata)
    ↓
Tool Registry (central source of truth, validates on registration)
    ↓
MultiToolSelector (works directly with BaseTool instances)
```

## Phase 1: Consolidate Tool Model (Priority)

### 1.1 `tool_selection/base_tool.py` - Create Unified Tool Model

**Current State:**
```python
class ToolMetadata(BaseModel):
    name: str
    description: str
    category: str
    args_model: Optional[Type[BaseModel]] = None

class BaseTool(BaseModel):
    metadata: ToolMetadata
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        pass
```

**Proposed Unified Model:**
```python
from typing import List, ClassVar, Type, Any, Optional, Dict
from pydantic import BaseModel, Field, field_validator
from abc import ABC, abstractmethod

class ToolArgument(BaseModel):
    """Unified argument definition used everywhere."""
    name: str = Field(..., pattern="^[a-zA-Z_][a-zA-Z0-9_]*$")  # Valid Python identifier
    type: str = Field(..., description="Python type name (e.g., 'str', 'int', 'float')")
    description: str = Field(..., min_length=1)
    required: bool = Field(default=True)
    default: Optional[Any] = None

class BaseTool(BaseModel, ABC):
    """Unified tool class that serves as both definition and implementation."""
    
    # Class-level constants (not Pydantic fields)
    NAME: ClassVar[str]  # Must be defined by each tool
    MODULE: ClassVar[str]  # Must be defined by each tool
    
    # Instance fields that define the tool
    description: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    arguments: List[ToolArgument] = Field(default_factory=list)
    
    # Optional: Pydantic model for argument validation
    args_model: Optional[Type[BaseModel]] = Field(default=None, exclude=True)
    
    def __init_subclass__(cls, **kwargs):
        """Validate that subclasses define required class variables."""
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, 'NAME'):
            raise TypeError(f"{cls.__name__} must define NAME class variable")
        if not hasattr(cls, 'MODULE'):
            raise TypeError(f"{cls.__name__} must define MODULE class variable")
        # Validate NAME is a valid Python identifier
        if not cls.NAME.isidentifier():
            raise ValueError(f"{cls.__name__}.NAME must be a valid Python identifier, got: {cls.NAME}")
    
    @property
    def name(self) -> str:
        """Tool name from class constant."""
        return self.NAME
    
    @field_validator('arguments', mode='before')
    @classmethod
    def populate_arguments_from_model(cls, v, info):
        """Auto-populate arguments from args_model if not provided."""
        if not v and 'args_model' in info.data and info.data['args_model']:
            return cls._extract_arguments_from_model(info.data['args_model'])
        return v
    
    @classmethod
    def _extract_arguments_from_model(cls, model: Type[BaseModel]) -> List[ToolArgument]:
        """Extract ToolArgument list from a Pydantic model."""
        schema = model.model_json_schema()
        properties = schema.get('properties', {})
        required = schema.get('required', [])
        
        arguments = []
        for field_name, field_info in properties.items():
            arguments.append(ToolArgument(
                name=field_name,
                type=field_info.get('type', 'string'),
                description=field_info.get('description', ''),
                required=field_name in required,
                default=field_info.get('default')
            ))
        return arguments
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with validated arguments."""
        pass
    
    def validate_and_execute(self, **kwargs) -> Dict[str, Any]:
        """Validate arguments using args_model before execution."""
        if self.args_model:
            # Validate using Pydantic model
            validated_args = self.args_model(**kwargs)
            return self.execute(**validated_args.model_dump())
        return self.execute(**kwargs)
```

### 1.2 Example Tool Implementation

**Before (multiple models):**
```python
@register_tool
class GiveHintTool(BaseTool):
    NAME: ClassVar[str] = "give_hint"
    MODULE: ClassVar[str] = "tools.treasure_hunt.give_hint"
    
    class Arguments(BaseModel):
        hint_total: int = Field(default=0, ge=0)
    
    metadata = ToolMetadata(
        name=NAME,
        description="Give a progressive hint about the treasure location",
        category="treasure_hunt",
        args_model=Arguments
    )
    
    def execute(self, hint_total: int = 0) -> dict:
        # implementation
```

**After (unified model):**
```python
@register_tool
class GiveHintTool(BaseTool):
    NAME: ClassVar[str] = "give_hint"
    MODULE: ClassVar[str] = "tools.treasure_hunt.give_hint"
    
    class Arguments(BaseModel):
        """Argument validation model."""
        hint_total: int = Field(
            default=0, 
            ge=0, 
            description="The total number of hints already given"
        )
    
    # Tool definition as instance attributes
    description: str = "Give a progressive hint about the treasure location"
    category: str = "treasure_hunt"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, hint_total: int = 0) -> Dict[str, Any]:
        """Execute the tool to give a hint."""
        hints = [
            "The treasure is in a city known for its coffee and rain.",
            "It's located near a famous public market.",
            "The address is on a street named after a US President's wife."
        ]
        
        if hint_total < len(hints):
            return {"hint": hints[hint_total]}
        else:
            return {"hint": "No more hints available."}
```

### 1.3 `tool_selection/models.py` - Remove Redundant Models

**Actions:**
- Delete `MultiToolName` enum entirely
- Delete `MultiTool` class (tools ARE their own definition now)
- Keep only `ToolArgument` if not moved to base_tool.py
- Keep `ToolCall` and `MultiToolDecision` for selector output

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class ToolCall(BaseModel):
    """A single tool invocation with arguments."""
    tool_name: str = Field(..., description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool")

class MultiToolDecision(BaseModel):
    """Decision about which tools to use."""
    reasoning: str = Field(..., description="Explanation of why these tools were selected")
    tool_calls: List[ToolCall] = Field(..., description="List of tools to call with their arguments")
```

## Phase 2: Update Components to Use Unified Model

### 2.1 `tool_selection/multi_tool_selector.py`

**Actions:**
- Update to work directly with `BaseTool` instances
- Use dynamic signatures based on available tools
- Leverage DSPy best practices

**Proposed Implementation:**
```python
import dspy
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from tool_selection.base_tool import BaseTool
from tool_selection.models import ToolCall, MultiToolDecision

class ToolSelectionSignature(dspy.Signature):
    """Select appropriate tools based on user request."""
    request: str = dspy.InputField(desc="The user's request")
    available_tools: str = dspy.InputField(
        desc="Available tools with descriptions in format: tool_name: description"
    )
    reasoning: str = dspy.OutputField(
        desc="Step-by-step reasoning about which tools to use and why"
    )
    selected_tools: str = dspy.OutputField(
        desc="Comma-separated list of selected tool names"
    )
    tool_arguments: str = dspy.OutputField(
        desc="JSON object mapping tool names to their arguments"
    )

class MultiToolSelector(dspy.Module):
    """Selects appropriate tools based on user request."""
    
    def __init__(self, use_chain_of_thought: bool = True):
        super().__init__()
        if use_chain_of_thought:
            self.predictor = dspy.ChainOfThought(ToolSelectionSignature)
        else:
            self.predictor = dspy.Predict(ToolSelectionSignature)
    
    def forward(self, request: str, tools: List[BaseTool]) -> MultiToolDecision:
        """Select tools based on request using available tools."""
        # Create tool descriptions for the LLM
        tool_descriptions = []
        tool_map = {}
        
        for tool in tools:
            # Build argument description
            arg_desc = []
            for arg in tool.arguments:
                arg_str = f"{arg.name}: {arg.type}"
                if arg.description:
                    arg_str += f" - {arg.description}"
                if not arg.required:
                    arg_str += " (optional)"
                arg_desc.append(arg_str)
            
            # Format: "tool_name: description. Arguments: [arg1: type - desc, ...]"
            tool_desc = f"{tool.name}: {tool.description}"
            if arg_desc:
                tool_desc += f". Arguments: [{', '.join(arg_desc)}]"
            
            tool_descriptions.append(tool_desc)
            tool_map[tool.name] = tool
        
        available_tools_str = "\n".join(tool_descriptions)
        
        # Get prediction from DSPy
        result = self.predictor(
            request=request,
            available_tools=available_tools_str
        )
        
        # Parse selected tools and arguments
        import json
        selected_tool_names = [t.strip() for t in result.selected_tools.split(",")]
        
        try:
            tool_args = json.loads(result.tool_arguments) if result.tool_arguments else {}
        except json.JSONDecodeError:
            tool_args = {}
        
        # Build tool calls, validating against available tools
        tool_calls = []
        for tool_name in selected_tool_names:
            if tool_name in tool_map:
                tool_calls.append(ToolCall(
                    tool_name=tool_name,
                    arguments=tool_args.get(tool_name, {})
                ))
        
        return MultiToolDecision(
            reasoning=result.reasoning,
            tool_calls=tool_calls
        )
```

**DSPy Best Practices Applied:**
- Clear, descriptive `InputField` and `OutputField` definitions
- Structured format for tool descriptions that LLM can parse
- Chain-of-Thought for better reasoning
- JSON format for structured argument extraction

### 2.2 `tool_selection/multi_demo.py`

**Actions:**
- Remove `convert_tools_to_definitions()` function entirely
- Work directly with `BaseTool` instances
- Simplify the demo to use the unified model

**Before:**
```python
def convert_tools_to_definitions() -> List[MultiTool]:
    """Convert registered tools to the format expected by MultiToolSelector."""
    # ... lots of conversion logic
    return definitions

def run_demo():
    # Load tools from tool sets
    load_tools_from_sets(tool_sets)
    
    # Get tool definitions and test cases
    tool_definitions = convert_tools_to_definitions()
    
    # Initialize selector
    selector = MultiToolSelector()
    
    # Get decision
    decision = selector(test_case.request, tool_definitions)
```

**After:**
```python
def run_demo():
    # Load tools from tool sets
    load_tools_from_sets(tool_sets)
    
    # Get tools directly from registry - no conversion needed!
    tools = list(registry.get_all_tools().values())
    
    # Initialize selector
    selector = MultiToolSelector()
    
    # Get decision - selector works directly with BaseTool instances
    decision = selector(test_case.request, tools)
```

**Reason:** No conversion needed since tools are already in the right format.

### 2.3 `tool_selection/registry.py`

**Actions:**
- Update type hints to use string tool names
- Add validation when registering tools
- Ensure tool names are unique and valid identifiers

**Updated Registry:**
```python
from typing import Dict, Type, Callable, List, Optional
from tool_selection.base_tool import BaseTool

class ToolRegistry:
    """Central registry for all tools."""
    
    def __init__(self):
        self._tools: Dict[str, Type[BaseTool]] = {}
        self._instances: Dict[str, BaseTool] = {}
    
    def register(self, tool_class: Type[BaseTool]) -> None:
        """Register a tool class."""
        # Validation happens in BaseTool.__init_subclass__
        tool_name = tool_class.NAME
        
        if tool_name in self._tools:
            raise ValueError(f"Tool '{tool_name}' is already registered")
        
        self._tools[tool_name] = tool_class
        
        # Create and cache tool instance
        # Tools are now Pydantic models with fields
        instance = tool_class()
        self._instances[tool_name] = instance
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool instance by name."""
        return self._instances.get(name)
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """Get all registered tool instances."""
        return self._instances.copy()
    
    def get_tool_names(self) -> List[str]:
        """Get names of all registered tools."""
        return list(self._tools.keys())
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name with given arguments."""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        # Use the new validate_and_execute method
        return tool.validate_and_execute(**kwargs)

# Global registry instance
registry = ToolRegistry()

def register_tool(cls: Type[BaseTool]) -> Type[BaseTool]:
    """Decorator to register a tool."""
    registry.register(cls)
    return cls
```

## How This Prevents Type Safety Issues and Typos

### 1. **Tool Names as Static Constants**
```python
# Tool name is defined ONCE as a class constant
class GiveHintTool(BaseTool):
    NAME: ClassVar[str] = "give_hint"  # Single source of truth
```

### 2. **Validation at Multiple Levels**

**At Tool Definition (compile time):**
```python
def __init_subclass__(cls, **kwargs):
    """Validate that subclasses define required class variables."""
    if not hasattr(cls, 'NAME'):
        raise TypeError(f"{cls.__name__} must define NAME class variable")
    if not cls.NAME.isidentifier():
        raise ValueError(f"{cls.__name__}.NAME must be a valid Python identifier")
```

**At Registration (startup time):**
```python
def register(self, tool_class: Type[BaseTool]) -> None:
    if tool_name in self._tools:
        raise ValueError(f"Tool '{tool_name}' is already registered")
```

**At Argument Level (via Pydantic):**
```python
class ToolArgument(BaseModel):
    name: str = Field(..., pattern="^[a-zA-Z_][a-zA-Z0-9_]*$")  # Valid identifier
    type: str = Field(..., description="Python type name")
    description: str = Field(..., min_length=1)  # Non-empty
```

### 3. **No String Literals in Code**
```python
# Always use class constants, never strings
tool_set.add(GiveHintTool)  # ✓ Class reference
tool_name = GiveHintTool.NAME  # ✓ Class constant

# Never this:
tool_set.add("give_hint")  # ✗ Magic string
```

## Benefits of This Approach

1. **Single Source of Truth**: Each tool defines its name ONCE as a class constant
2. **Type Safety**: Pydantic validates all fields at runtime
3. **No Magic Strings**: Always use class references and constants
4. **Dynamic Loading**: New tools can be added without modifying any enums
5. **Simplified Code**: No conversion functions or redundant models
6. **Better Developer Experience**: Clear error messages at multiple validation points
7. **Maintainability**: Tool definition and implementation in one place

## Implementation Steps

### Phase 1: Core Refactoring (Priority)
1. **Update `base_tool.py`**: Implement the unified `BaseTool` model
2. **Update `models.py`**: Remove `MultiToolName` enum and `MultiTool` class
3. **Update existing tools**: Migrate to the new unified model pattern

### Phase 2: Component Updates
1. **Update `registry.py`**: Implement the new registry with validation
2. **Update `multi_tool_selector.py`**: Work directly with `BaseTool` instances
3. **Update `multi_demo.py`**: Remove conversion functions

### Phase 3: Testing and Migration
1. **Update all tests**: Remove enum references, use tool constants
2. **Add new tests**: Test validation at all levels
3. **Migration guide**: Document how to update existing tools

### Phase 4: Extension
1. **Update remaining tool domains**: Apply pattern to events, ecommerce, finance tools
2. **Documentation**: Update README and examples
3. **Performance optimization**: Cache tool descriptions for selector

## Potential Risks and Mitigations

### Risk 1: Type Safety
**Issue**: Losing compile-time type checking for tool names
**Mitigation**: 
- Add runtime validation in the registry
- Use string constants (CLASS.NAME) instead of string literals
- Consider using TypedDict for tool schemas

### Risk 2: Typos in Tool Names
**Issue**: Without enum validation, typos could cause runtime errors
**Mitigation**:
- Validate tool names are valid Python identifiers
- Add comprehensive tests
- Use tool class NAME constants consistently

### Risk 3: DSPy Performance
**Issue**: Dynamic signatures might affect DSPy optimization
**Mitigation**:
- Cache signature classes per tool set
- Pre-compile common tool combinations
- Monitor performance and optimize as needed

## Implementation Steps

1. **Phase 1**: Update tool infrastructure
   - Modify registry to use strings
   - Update MultiTool model
   - Remove MultiToolName enum

2. **Phase 2**: Update DSPy components
   - Rewrite MultiToolSelector with dynamic signature
   - Test with various tool combinations
   - Optimize prompt engineering

3. **Phase 3**: Update tests and demos
   - Update all test files
   - Verify demos work with all tool sets
   - Add integration tests for dynamic loading

4. **Phase 4**: Documentation
   - Update README with new patterns
   - Document how to add new tools
   - Create migration guide

## Example: Adding a New Tool

With the unified model approach:

```python
# 1. Create the tool with all information in one place
@register_tool
class TranslateTextTool(BaseTool):
    NAME: ClassVar[str] = "translate_text"
    MODULE: ClassVar[str] = "tools.language.translate_text"
    
    class Arguments(BaseModel):
        """Validation model for arguments."""
        text: str = Field(..., min_length=1, description="Text to translate")
        target_language: str = Field(..., pattern="^[a-z]{2}$", description="ISO 639-1 language code")
        source_language: str = Field(default="auto", description="Source language (auto-detect by default)")
    
    # Tool definition
    description: str = "Translate text between languages"
    category: str = "language"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, text: str, target_language: str, source_language: str = "auto") -> Dict[str, Any]:
        """Execute translation."""
        # Implementation here
        return {"translated_text": f"[{target_language}] {text}"}

# 2. Add to a tool set - using class reference, not strings!
class LanguageToolSet(ToolSet):
    def __init__(self):
        super().__init__(
            config=ToolSetConfig(
                name="language",
                tool_classes=[TranslateTextTool]  # Class reference
            )
        )

# 3. Done! No enums, no conversions, no magic strings
```

## Example Usage in Code

```python
# Always use class constants
if tool.name == TranslateTextTool.NAME:  # ✓ Good
    pass

# Tool sets use class references
tool_set = ToolSet(
    config=ToolSetConfig(
        name="my_tools",
        tool_classes=[TranslateTextTool, GiveHintTool]  # ✓ Good
    )
)

# Registry works with instances
tool = registry.get_tool(TranslateTextTool.NAME)  # ✓ Good

# Selector works directly with tools
decision = selector(request, [tool1, tool2, tool3])  # ✓ Good
```

## Conclusion

This proposal creates a cleaner, more maintainable architecture by:

1. **Consolidating to a single tool model** that serves as both definition and implementation
2. **Leveraging Pydantic** for type safety and validation throughout
3. **Using class constants** instead of magic strings
4. **Making the registry the single source of truth** for available tools
5. **Eliminating all conversion layers** between different representations

The result is a system that is easier to understand, extend, and maintain while providing better type safety and developer experience.