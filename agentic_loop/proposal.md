# Agentic Loop Implementation - Class Organization

## Directory Structure

```
agentic_loop/
├── __init__.py                    # Public API exports
├── models.py                      # Core data models (some *REUSE* from tool_selection)
├── agent_reasoner.py              # Core reasoning module with DSPy
├── agent_loop.py                  # Main ManualAgentLoop class
├── activity_manager.py            # External control and execution
├── tool_registry_adapter.py       # Adapter for existing tool registries
├── conversation_manager.py        # Conversation history management
├── error_recovery.py              # Error handling and recovery strategies
├── response_formatter.py          # Response formatting modules
├── tool_sets.py                   # Agentic-specific tool sets
└── tools/                         # Agentic-specific tools
    ├── __init__.py
    ├── reasoning/
    │   ├── __init__.py
    │   ├── analyze_progress.py
    │   └── plan_next_steps.py
    └── control/
        ├── __init__.py
        ├── check_goal.py
        └── terminate_loop.py
```

## Class Organization and Reusability Analysis

### 1. Core Data Models (`models.py`)

#### *REUSE* from `tool_selection/models.py`:
```python
# These models work perfectly for agentic loops
from tool_selection.models import ToolCall, MultiToolDecision  # *REUSE*
```

#### New Models for Agentic Loops:
```python
class ActionType(str, Enum):
    """Types of actions the agent can suggest."""
    TOOL_EXECUTION = "tool_execution"
    FINAL_RESPONSE = "final_response"
    ERROR_RECOVERY = "error_recovery"
    GOAL_CHECK = "goal_check"

class ReasoningOutput(BaseModel):
    """Unified reasoning output combining tool selection and continuation decisions."""
    overall_reasoning: str = Field(desc="High-level reasoning about current state and next steps")
    confidence: float = Field(ge=0, le=1, desc="Confidence in the decision (0-1)")
    
    # Tool selection
    should_use_tools: bool = Field(desc="Whether tools should be called in this iteration")
    tool_calls: Optional[List[ToolCall]] = Field(None, desc="List of tools to execute if should_use_tools is True")
    parallel_safe: bool = Field(default=True, desc="Whether suggested tools can be executed in parallel")
    
    # Continuation decision
    should_continue: bool = Field(desc="Whether to continue after this iteration")
    continuation_reasoning: str = Field(desc="Specific reasoning about whether to continue or stop")
    
    # Final response (if not continuing)
    final_response: Optional[str] = Field(None, desc="Final response to user if not continuing")
    suggested_next_action: Optional[str] = Field(None, desc="Hint about what might be needed next")

class ActionDecision(BaseModel):
    """Decision returned by the agent for external execution control."""
    action_type: ActionType
    reasoning: str
    confidence: float = Field(ge=0, le=1)
    
    # For tool execution
    tool_suggestions: Optional[List[ToolCall]] = None
    parallel_safe: bool = Field(default=True)
    
    # For final response
    final_response: Optional[str] = None
    
    # For continuation
    should_continue: bool = Field(default=True)
    suggested_next_action: Optional[str] = None
    
    # Metadata
    processing_time: float = Field(default=0)
    tokens_used: Optional[int] = None

class ConversationState(BaseModel):
    """Complete conversation state for stateless operation."""
    user_query: str
    goal: Optional[str] = None  # Optional explicit goal
    iteration_count: int = 0
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    last_tool_results: Optional[List[Dict[str, Any]]] = None
    total_tool_calls: int = 0
    errors_encountered: List[str] = Field(default_factory=list)
    
    # ActivityManager metadata
    activity_id: Optional[str] = None
    max_iterations: Optional[int] = None
    start_time: Optional[float] = None
    last_confidence: Optional[float] = None
```

### 2. Agent Reasoning (`agent_reasoner.py`)

#### *REUSE* Patterns from `tool_selection/multi_tool_selector.py`:
```python
# Reuse the signature creation patterns and type safety approach
# The dynamic signature generation with Literal types is excellent
from tool_selection.multi_tool_selector import MultiToolSelector  # *REUSE* patterns
```

#### New Agentic Reasoning Module:
```python
class AgentReasonerSignature(dspy.Signature):
    """Unified reasoning signature for agentic loops."""
    user_query: str = dspy.InputField(desc="The user's original request")
    goal: Optional[str] = dspy.InputField(desc="Explicit goal if provided")
    conversation_history: str = dspy.InputField(desc="Previous tool calls and their results")
    last_tool_results: Optional[str] = dspy.InputField(desc="Results from most recent tool executions")
    available_tools: str = dspy.InputField(desc="JSON array of available tools and descriptions")
    iteration_count: int = dspy.InputField(desc="Current iteration number")
    max_iterations: int = dspy.InputField(desc="Maximum allowed iterations")
    
    reasoning_output: ReasoningOutput = dspy.OutputField(desc="Combined reasoning and decision output")

class AgentReasoner(dspy.Module):
    """Core reasoning module for agentic loops."""
    
    def __init__(self, tool_names: List[str], max_iterations: int = 5):
        super().__init__()
        self.tool_names = tool_names
        self.max_iterations = max_iterations
        
        # Main reasoning with Chain of Thought
        self.reasoner = dspy.ChainOfThought(AgentReasonerSignature)
        
        # History summarizer for long conversations
        self.history_summarizer = dspy.Predict(
            "long_history -> summary:str, key_points:list[str]"
        )
    
    def forward(self, user_query: str, goal: Optional[str], conversation_history: str, 
                last_tool_results: Optional[str], available_tools: str, 
                iteration_count: int) -> dspy.Prediction:
        """Execute unified reasoning about next action."""
        # Implementation follows the hybrid approach from the original proposal
        # ...
```

### 3. Tool Registry Integration (`tool_registry_adapter.py`)

#### *REUSE* from `tool_selection/registry.py` and `tool_selection/tool_sets.py`:
```python
# The entire registry pattern can be reused with minimal adaptation
from tool_selection.registry import ToolRegistry, registry  # *REUSE*
from tool_selection.tool_sets import ToolSet, ToolSetRegistry, tool_set_registry  # *REUSE*
from tool_selection.base_tool import BaseTool  # *REUSE*
```

#### Simple Tool Set Selection Approach:
```python
class AgenticToolSetManager:
    """Simple tool set manager for agentic loops."""
    
    def __init__(self):
        self.current_tool_set: Optional[str] = None
        self.available_tool_sets = {
            "treasure_hunt": ["give_hint", "guess_location"],
            "productivity": ["set_reminder"],
            "ecommerce": ["get_order", "list_orders", "add_to_cart", "search_products", "track_order", "return_item"],
            "reasoning": ["analyze_progress", "plan_next_steps"],  # New agentic tools
            "control": ["check_goal", "terminate_loop"]  # New agentic tools
        }
    
    def load_tool_set(self, tool_set_name: str) -> List[str]:
        """Load a specific tool set and return available tool names."""
        if tool_set_name not in self.available_tool_sets:
            raise ValueError(f"Unknown tool set: {tool_set_name}")
        
        # Clear and load the specified tool set
        from tool_selection.tool_sets import tool_set_registry  # *REUSE*
        tool_set_registry.load_tool_set(tool_set_name)
        
        self.current_tool_set = tool_set_name
        return self.available_tool_sets[tool_set_name]
    
    def get_current_tools(self) -> List[str]:
        """Get currently loaded tool names."""
        if not self.current_tool_set:
            return []
        return self.available_tool_sets[self.current_tool_set]

class DSPyToolRegistryAdapter:
    """Adapter for existing tool registries - *REUSE* pattern."""
    
    def __init__(self, existing_registry=None):
        # Use global registry if none provided
        self.registry = existing_registry or registry  # *REUSE*
    
    def get_tool(self, tool_name: str) -> callable:
        """Get tool with error handling."""
        tool = self.registry.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found in registry")
        return tool.validate_and_execute  # *REUSE* validation pattern
    
    def get_all_tool_names(self) -> List[str]:
        """Get tool names."""
        return self.registry.get_tool_names()  # *REUSE*
    
    def get_all_tool_descriptions(self) -> List[Dict[str, Any]]:
        """Convert tool definitions to standardized format."""
        descriptions = []
        for tool_name in self.get_all_tool_names():
            tool = self.registry.get_tool(tool_name)
            if tool:
                desc = {
                    "name": tool_name,
                    "description": tool.description,
                    "parameters": []
                }
                
                # Extract parameters from args_model
                if hasattr(tool, 'args_model') and tool.args_model:
                    for field_name, field_info in tool.args_model.model_fields.items():
                        desc["parameters"].append({
                            "name": field_name,
                            "type": str(field_info.annotation),
                            "description": field_info.description or "",
                            "required": field_info.is_required()
                        })
                
                descriptions.append(desc)
        
        return descriptions
```

### 4. Main Agent Loop (`agent_loop.py`)

#### *REUSE* Patterns from `tool_selection/`:
```python
# Reuse the modular architecture and validation patterns
from tool_selection.base_tool import BaseTool  # *REUSE*
```

#### New ManualAgentLoop Class:
```python
class ManualAgentLoop(dspy.Module):
    """Stateless agent loop for external control."""
    
    def __init__(self, tool_set_name: str, enable_error_recovery: bool = True):
        super().__init__()
        
        # Simple tool set selection
        self.tool_set_manager = AgenticToolSetManager()
        available_tools = self.tool_set_manager.load_tool_set(tool_set_name)
        
        # Tool registry adapter
        self.tool_registry = DSPyToolRegistryAdapter()
        
        # Core reasoning
        self.agent_reasoner = AgentReasoner(
            tool_names=available_tools,
            max_iterations=10
        )
        
        # Optional modules
        if enable_error_recovery:
            self.error_recovery = ErrorRecoveryModule()
        
        self.response_formatter = ResponseFormatter()
    
    def get_next_action(self, state: ConversationState) -> ActionDecision:
        """Main entry point for ActivityManager."""
        # Implementation follows the stateless pattern from original proposal
        # ...
```

### 5. Activity Manager (`activity_manager.py`)

#### New External Control Class:
```python
class ActivityManager:
    """External controller for agent loops with simple tool set selection."""
    
    def __init__(self, tool_set_name: str, max_iterations: int = 10):
        self.tool_set_name = tool_set_name
        self.max_iterations = max_iterations
        
        # Create agent with specified tool set
        self.agent_loop = ManualAgentLoop(
            tool_set_name=tool_set_name,
            enable_error_recovery=True
        )
        
        # Tool registry for execution
        self.tool_registry = DSPyToolRegistryAdapter()
        
        # Execution control
        self.executor = ThreadPoolExecutor(max_workers=3)
    
    def run_activity(self, user_query: str, goal: Optional[str] = None, 
                    activity_id: str = None) -> Dict[str, Any]:
        """Run complete activity with specified tool set."""
        # Implementation follows the external control pattern
        # ...
```

### 6. Agentic Tool Sets (`tool_sets.py`)

#### *REUSE* from `tool_selection/tool_sets.py`:
```python
# Reuse the entire tool set architecture
from tool_selection.tool_sets import ToolSet, ToolSetConfig, ToolSetTestCase  # *REUSE*
```

#### New Agentic Tool Sets:
```python
class ReasoningToolSet(ToolSet):
    """Tool set for agentic reasoning capabilities."""
    NAME: ClassVar[str] = "reasoning"
    
    def __init__(self):
        from .tools.reasoning.analyze_progress import AnalyzeProgressTool
        from .tools.reasoning.plan_next_steps import PlanNextStepsTool
        
        super().__init__(
            config=ToolSetConfig(
                name=self.NAME,
                description="Tools for agentic reasoning and planning",
                tool_classes=[
                    AnalyzeProgressTool,
                    PlanNextStepsTool
                ]
            )
        )

class ControlToolSet(ToolSet):
    """Tool set for agentic loop control."""
    NAME: ClassVar[str] = "control"
    
    def __init__(self):
        from .tools.control.check_goal import CheckGoalTool
        from .tools.control.terminate_loop import TerminateLoopTool
        
        super().__init__(
            config=ToolSetConfig(
                name=self.NAME,
                description="Tools for agentic loop control and termination",
                tool_classes=[
                    CheckGoalTool,
                    TerminateLoopTool
                ]
            )
        )
```

### 7. Error Recovery (`error_recovery.py`)

#### New Error Recovery Module:
```python
class ErrorRecoveryModule(dspy.Module):
    """Specialized error recovery for agentic loops."""
    
    def __init__(self):
        super().__init__()
        self.recovery_planner = dspy.ChainOfThought(
            "error_info, available_tools, iteration_count -> recovery_strategy:str, alternative_actions:list[str]"
        )
    
    # Implementation follows the specialized approach from original proposal
```

## Simple Tool Set Selection Design

### Approach: Static Tool Set Selection at Startup

1. **No Dynamic Switching**: Tool sets are selected when the ActivityManager is created
2. **Clear Separation**: Each tool set is completely independent
3. **Simple Configuration**: Just specify the tool set name when starting

### Usage Examples:

```python
# Treasure Hunt Activity
treasure_manager = ActivityManager(tool_set_name="treasure_hunt")
result = treasure_manager.run_activity("Help me find the treasure!")

# Productivity Activity
productivity_manager = ActivityManager(tool_set_name="productivity")
result = productivity_manager.run_activity("Remind me to call mom at 5pm")

# E-commerce Activity
ecommerce_manager = ActivityManager(tool_set_name="ecommerce")
result = ecommerce_manager.run_activity("Check my order status for order #12345")

# Agentic Reasoning Activity
reasoning_manager = ActivityManager(tool_set_name="reasoning")
result = reasoning_manager.run_activity("Plan the next steps for my project")
```

## Component Reusability Summary

### ✅ **High Reuse Components**:
- `BaseTool` class and validation patterns
- `ToolRegistry` and `@register_tool` decorator
- `ToolSet` architecture and `ToolSetRegistry`
- `ToolCall` and `MultiToolDecision` models
- Tool organization and loading patterns
- Test case patterns and structures

### 🔄 **Partial Reuse Components**:
- `MultiToolSelector` patterns (adapt for agentic reasoning)
- Dynamic signature generation (extend for conversation state)
- Tool execution patterns (add iteration context)

### ❌ **New Components Needed**:
- `ReasoningOutput` and `ActionDecision` models
- `ConversationState` and history management
- `AgentReasoner` with unified reasoning
- `ActivityManager` for external control
- Error recovery strategies for loops
- Agentic-specific tool implementations

## Implementation Priority

1. **Phase 1**: Set up basic models and tool registry adapter (*REUSE* heavy)
2. **Phase 2**: Create `AgentReasoner` with simple tool selection 
3. **Phase 3**: Implement `ManualAgentLoop` with stateless operation
4. **Phase 4**: Build `ActivityManager` with simple tool set selection
5. **Phase 5**: Add error recovery and response formatting
6. **Phase 6**: Create agentic-specific tool sets and tools
7. **Phase 7**: Testing and integration with existing patterns

This design maximizes reuse of the excellent existing patterns while cleanly separating agentic-specific concerns.