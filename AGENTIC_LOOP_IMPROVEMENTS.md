# Agentic Loop Improvements Proposal

## Current State Analysis

The current agentic loop implementation has several limitations when handling multi-step tasks:

1. **Fixed iteration limit**: Currently hardcoded to 3 iterations in most cases
2. **Limited tool result feedback**: Tool results are passed to the next iteration but not deeply analyzed
3. **No dynamic adaptation**: The loop doesn't adjust its strategy based on tool execution results
4. **Incomplete task detection**: No mechanism to detect when a multi-step task is only partially complete

## Proposed Improvements

### 1. Dynamic Iteration Management

Update the `ActivityManager` to support dynamic iteration limits based on task complexity:

```python
# In activity_manager.py
class ActivityManager:
    def __init__(
        self,
        agent_loop: ManualAgentLoop,
        tool_registry: ToolRegistry,
        max_iterations: int = 10,  # Increase default
        min_iterations: int = 2,   # Add minimum
        timeout_seconds: float = 60.0,
        dynamic_iterations: bool = True  # Enable dynamic adjustment
    ):
```

### 2. Enhanced Tool Result Analysis

Add a DSPy module to analyze tool results and determine next steps:

```python
# In agent_reasoner.py
class ToolResultAnalyzer(dspy.Module):
    """Analyzes tool execution results to guide next actions."""
    
    def __init__(self):
        super().__init__()
        self.analyzer = dspy.ChainOfThought(
            "tool_name, tool_result, original_goal -> "
            "is_successful: bool, needs_followup: bool, "
            "suggested_next_tools: list[str], reasoning: str"
        )
```

### 3. Goal Completion Tracking

Implement a goal tracking system that monitors progress:

```python
# In shared/models.py
class GoalProgress(BaseModel):
    """Tracks progress toward completing a goal."""
    original_goal: str
    sub_goals: List[str] = Field(default_factory=list)
    completed_steps: List[str] = Field(default_factory=list)
    pending_steps: List[str] = Field(default_factory=list)
    completion_percentage: float = 0.0
    
# In agent_reasoner.py
class GoalTracker(dspy.Module):
    """Tracks and evaluates goal completion progress."""
    
    def __init__(self):
        super().__init__()
        self.goal_analyzer = dspy.ChainOfThought(
            "original_goal, tool_results, conversation_history -> "
            "goal_progress: GoalProgress, should_continue: bool"
        )
```

### 4. Improved AgentReasonerSignature

Update the signature to include more context about tool results:

```python
class AgentReasonerSignature(dspy.Signature):
    """Enhanced signature with tool result analysis."""
    
    # Existing fields
    user_query: str = dspy.InputField(desc="The user's request or query")
    goal: str = dspy.InputField(desc="The goal to achieve")
    conversation_history: str = dspy.InputField(desc="Previous conversation context")
    last_tool_results: str = dspy.InputField(desc="Results from most recent tool executions")
    available_tools: str = dspy.InputField(desc="JSON description of available tools")
    iteration_count: int = dspy.InputField(desc="Current iteration number")
    max_iterations: int = dspy.InputField(desc="Maximum allowed iterations")
    
    # New fields
    goal_progress: str = dspy.InputField(desc="Current progress toward goal completion")
    successful_tools: str = dspy.InputField(desc="List of successfully executed tools")
    
    # Enhanced output
    reasoning_output: ReasoningOutput = dspy.OutputField(
        desc="Structured output with reasoning, tool selections, and completion status"
    )
```

### 5. Multi-Step Task Templates

Create templates for common multi-step patterns:

```python
# In agentic_loop/task_templates.py
class TaskTemplate(BaseModel):
    """Template for multi-step task patterns."""
    name: str
    pattern: str  # e.g., "search_and_select", "verify_and_modify"
    required_tools: List[str]
    typical_iterations: int
    
COMMON_TEMPLATES = {
    "search_and_select": TaskTemplate(
        name="Search and Select",
        pattern="search_and_select",
        required_tools=["search_products", "add_to_cart"],
        typical_iterations=4  # Search, review results, select, add
    ),
    "verify_and_modify": TaskTemplate(
        name="Verify and Modify",
        pattern="verify_and_modify", 
        required_tools=["get_order", "list_orders", "return_item"],
        typical_iterations=5  # List, get details, verify, decide, execute
    )
}
```

### 6. Implementation Example

Here's how the improved flow would work:

```python
# In manual_agent_loop.py
def get_next_action(self, state: ConversationState) -> ActionDecision:
    """Enhanced action decision with goal tracking."""
    
    # Analyze previous tool results if available
    tool_result_analysis = ""
    if state.last_tool_results:
        analysis = self.tool_result_analyzer(
            tool_results=state.last_tool_results,
            original_goal=state.goal or state.user_query
        )
        tool_result_analysis = analysis.reasoning
        
        # Check if we need more iterations
        if analysis.needs_followup and state.iteration_count >= state.max_iterations:
            # Request more iterations if task incomplete
            state.max_iterations = min(state.max_iterations + 3, 10)
    
    # Track goal progress
    goal_progress = self.goal_tracker(
        original_goal=state.goal or state.user_query,
        tool_results=self._format_all_tool_results(state),
        conversation_history=self._format_conversation_history(state)
    )
    
    # Enhanced reasoning with all context
    reasoning_result = self.agent_reasoner(
        user_query=state.user_query,
        goal=state.goal,
        conversation_history=self._format_conversation_history(state),
        last_tool_results=self._format_tool_results(state.last_tool_results),
        available_tools=self._format_available_tools(),
        iteration_count=state.iteration_count,
        max_iterations=state.max_iterations,
        goal_progress=str(goal_progress.goal_progress),
        successful_tools=self._get_successful_tools(state)
    )
    
    # Convert to action decision
    return self._convert_to_action_decision(reasoning_result.reasoning_output)
```

## Benefits

1. **Better Multi-Step Handling**: Tasks like "search and add to cart" will complete properly
2. **Adaptive Behavior**: The system adjusts iterations based on task complexity
3. **Goal Awareness**: Tracks progress and knows when a task is truly complete
4. **Improved Tool Selection**: Better understanding of which tools to use based on results
5. **DSPy Best Practices**: Leverages Chain of Thought for all complex decisions

## Implementation Priority

1. **Phase 1**: Increase default iterations and update Test Case 7 ✓
2. **Phase 2**: Add ToolResultAnalyzer for better result interpretation
3. **Phase 3**: Implement GoalTracker for progress monitoring
4. **Phase 4**: Add dynamic iteration adjustment
5. **Phase 5**: Create task templates for common patterns

## Configuration Options

Add to `.env`:

```bash
# Agentic Loop Configuration
AGENT_MAX_ITERATIONS=10
AGENT_MIN_ITERATIONS=2
AGENT_DYNAMIC_ITERATIONS=true
AGENT_TIMEOUT_SECONDS=120.0
AGENT_ENABLE_GOAL_TRACKING=true
```

## Testing Strategy

1. Create test cases that require 4-5 steps to complete
2. Test partial completion scenarios
3. Verify dynamic iteration adjustment works correctly
4. Ensure timeout protection still functions
5. Test with all three tool sets (treasure_hunt, productivity, ecommerce)