# DSPy Manual Agent Loop Implementation

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

## Detailed Component Design

### 1. Core Agent Reasoning Module (Hybrid Approach)

```python
import dspy
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional
from enum import Enum

# Pydantic models for structured outputs
class ToolCall(BaseModel):
    """Represents a single tool call with parameters."""
    tool_name: str = Field(desc="Name of the tool to execute")
    parameters: Dict[str, Any] = Field(desc="Parameters to pass to the tool")
    reasoning: str = Field(desc="Why this tool is needed for the task")

class ReasoningOutput(BaseModel):
    """Combined output for reasoning about next steps."""
    # Overall reasoning
    overall_reasoning: str = Field(desc="High-level reasoning about the current state and next steps")
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
    suggested_next_action: Optional[str] = Field(None, desc="Hint about what might be needed next if continuing")

class AgentReasonerSignature(dspy.Signature):
    """Unified reasoning about tools and continuation in a single step."""
    
    user_query: str = dspy.InputField(desc="The user's original request")
    conversation_history: str = dspy.InputField(desc="Previous tool calls and their results")
    last_tool_results: Optional[str] = dspy.InputField(desc="Results from the most recent tool executions, if any")
    available_tools: str = dspy.InputField(desc="JSON array of available tools and their descriptions")
    iteration_count: int = dspy.InputField(desc="Current iteration number")
    max_iterations: int = dspy.InputField(desc="Maximum allowed iterations")
    
    reasoning_output: ReasoningOutput = dspy.OutputField(desc="Combined reasoning and decision output")

class AgentReasoner(dspy.Module):
    """Core reasoning module that handles both tool selection and continuation decisions."""
    
    def __init__(self, tool_names: List[str], max_iterations: int = 5):
        super().__init__()
        self.tool_names = tool_names
        self.max_iterations = max_iterations
        
        # Main reasoning with Chain of Thought for complex decisions
        self.reasoner = dspy.ChainOfThought(AgentReasonerSignature)
        
        # Optional: Validate reasoning output consistency
        self.output_validator = dspy.Predict(
            "reasoning_output -> is_valid:bool, validation_issues:list[str]"
        )
        
        # History summarizer for long conversations
        self.history_summarizer = dspy.Predict(
            "long_history -> summary:str, key_points:list[str]"
        )
    
    def forward(self, user_query: str, conversation_history: str, 
                last_tool_results: Optional[str], available_tools: str, 
                iteration_count: int) -> dspy.Prediction:
        """Execute unified reasoning about next action."""
        
        # Summarize history if too long
        if len(conversation_history) > 3000:
            summary_result = self.history_summarizer(long_history=conversation_history)
            conversation_history = (
                f"[Summarized earlier history]: {summary_result.summary}\n"
                f"Key points: {', '.join(summary_result.key_points)}\n\n"
                f"[Recent history]: {conversation_history[-1500:]}"
            )
        
        # Main reasoning
        result = self.reasoner(
            user_query=user_query,
            conversation_history=conversation_history,
            last_tool_results=last_tool_results or "No previous tool results",
            available_tools=available_tools,
            iteration_count=iteration_count,
            max_iterations=self.max_iterations
        )
        
        # Optional: Validate output consistency
        if hasattr(self, 'output_validator'):
            validation = self.output_validator(reasoning_output=result.reasoning_output)
            if not validation.is_valid:
                # Log validation issues but don't fail
                # In production, you might want to retry or handle differently
                pass
        
        return result
```

### 2. Specialized Error Recovery Module (Remains Separate)

### 3. Stateless Agent Loop for External Control

```python
import json
import time
from typing import List, Dict, Any, Optional, Union
from enum import Enum

class ActionType(str, Enum):
    """Type of action suggested by the agent."""
    TOOL_EXECUTION = "tool_execution"
    FINAL_RESPONSE = "final_response"
    ERROR_RECOVERY = "error_recovery"

class ActionDecision(BaseModel):
    """Decision returned by the agent for external execution."""
    action_type: ActionType
    reasoning: str
    confidence: float = Field(ge=0, le=1)
    
    # For tool execution
    tool_suggestions: Optional[List[ToolCall]] = None
    parallel_safe: bool = Field(default=True, desc="Whether tools can be executed in parallel")
    
    # For final response
    final_response: Optional[str] = None
    
    # For continuation
    should_continue: bool = Field(default=True)
    suggested_next_action: Optional[str] = None
    
    # Metadata
    processing_time: float = Field(default=0)
    tokens_used: Optional[int] = None

class ConversationState(BaseModel):
    """Complete conversation state passed between ActivityManager and Agent."""
    user_query: str
    iteration_count: int = 0
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    last_tool_results: Optional[List[Dict[str, Any]]] = None
    total_tool_calls: int = 0
    errors_encountered: List[str] = Field(default_factory=list)
    
    # ActivityManager metadata
    activity_id: Optional[str] = None
    max_iterations: Optional[int] = None
    start_time: Optional[float] = None

class ManualAgentLoop(dspy.Module):
    """Stateless agent loop designed for external control by ActivityManager."""
    
    def __init__(self, tool_registry, enable_error_recovery: bool = True):
        super().__init__()
        self.tool_registry = tool_registry
        self.enable_error_recovery = enable_error_recovery
        
        # Initialize DSPy modules
        tool_names = list(tool_registry.get_all_tool_names())
        self.tool_selector = ToolSelector(tool_names=tool_names)
        self.continuation_decider = ContinuationDecider()
        
        # Optional modules
        if enable_error_recovery:
            self.error_handler = ErrorHandler()
        
        self.response_generator = dspy.ChainOfThought(
            "user_query, conversation_summary, key_findings -> final_response"
        )
    
    def get_next_action(self, state: ConversationState) -> ActionDecision:
        """Get next action suggestion based on current state.
        
        This is the main entry point for ActivityManager to interact with the agent.
        Each call is stateless - all context is provided in the state parameter.
        """
        start_time = time.time()
        
        try:
            # Analyze current situation
            if state.last_tool_results and any(r.get("status") == "error" for r in state.last_tool_results):
                # Handle errors from previous tool execution
                return self._handle_tool_errors(state)
            
            # Check if we should generate final response
            if state.iteration_count > 0:
                decision = self._should_continue(state)
                if not decision.should_continue:
                    return self._create_final_response_action(state, decision)
            
            # Select next tools to execute
            tool_decision = self._select_next_tools(state)
            
            # Create action decision
            action = ActionDecision(
                action_type=ActionType.TOOL_EXECUTION,
                reasoning=tool_decision.reasoning,
                confidence=tool_decision.confidence,
                tool_suggestions=tool_decision.tool_calls,
                parallel_safe=tool_decision.parallel_execution,
                should_continue=True,
                suggested_next_action=tool_decision.next_action_hint,
                processing_time=time.time() - start_time
            )
            
            return action
            
        except Exception as e:
            # Return error recovery action
            return ActionDecision(
                action_type=ActionType.ERROR_RECOVERY,
                reasoning=f"Error in agent processing: {str(e)}",
                confidence=0.0,
                should_continue=False,
                final_response=self._generate_safe_error_response(state, e),
                processing_time=time.time() - start_time
            )
    
    def forward(self, state: ConversationState) -> ActionDecision:
        """DSPy-compatible forward method that delegates to get_next_action."""
        return self.get_next_action(state)
    
    def _select_next_tools(self, state: ConversationState) -> ToolSelectionOutput:
        """Select next tools to execute based on current state."""
        # Format conversation history
        history = self._format_conversation_history(state.conversation_history)
        
        # Format available tools
        tool_descriptions = self._format_tool_descriptions()
        
        # Add last tool results to history if available
        if state.last_tool_results:
            results_summary = self._format_tool_results(state.last_tool_results)
            history += f"\n\nLast tool results:\n{results_summary}"
        
        # Get tool selection
        selection_result = self.tool_selector(
            user_query=state.user_query,
            conversation_history=history,
            available_tools=tool_descriptions
        )
        
        # Enhance with additional metadata
        output = selection_result.output
        output.confidence = self._calculate_confidence(output, state)
        output.next_action_hint = self._generate_next_action_hint(output, state)
        
        return output
    
    def _should_continue(self, state: ConversationState) -> ContinuationDecision:
        """Decide if we should continue or provide final response."""
        history = self._format_conversation_history(state.conversation_history)
        results = self._format_tool_results(state.last_tool_results or [])
        
        decision = self.continuation_decider(
            user_query=state.user_query,
            conversation_history=history,
            last_tool_results=results,
            iteration_count=state.iteration_count
        )
        
        return decision.decision
    
    def _handle_tool_errors(self, state: ConversationState) -> ActionDecision:
        """Handle errors from previous tool execution."""
        if not self.enable_error_recovery:
            # Without error recovery, suggest final response
            return ActionDecision(
                action_type=ActionType.FINAL_RESPONSE,
                reasoning="Tool execution failed, providing best available response",
                confidence=0.6,
                should_continue=False,
                final_response=self._generate_error_response(state)
            )
        
        # Analyze errors and suggest recovery
        failed_tools = [r for r in state.last_tool_results if r.get("status") == "error"]
        recovery_suggestions = []
        
        for failed in failed_tools:
            recovery = self.error_handler(
                error_info=failed,
                user_query=state.user_query,
                available_tools=list(self.tool_registry.get_all_tool_names())
            )
            recovery_suggestions.append(recovery)
        
        # Create recovery action
        if any(r.strategy_type == "alternative_tool" for r in recovery_suggestions):
            # Suggest alternative tools
            alt_tools = []
            for recovery in recovery_suggestions:
                if recovery.strategy_type == "alternative_tool" and recovery.alternative_tool:
                    alt_tools.append(ToolCall(
                        tool_name=recovery.alternative_tool,
                        parameters={},  # Parameters need adjustment
                        reasoning=recovery.details
                    ))
            
            return ActionDecision(
                action_type=ActionType.TOOL_EXECUTION,
                reasoning="Attempting recovery with alternative tools",
                confidence=0.7,
                tool_suggestions=alt_tools,
                should_continue=True
            )
        
        # No recovery possible, suggest final response
        return ActionDecision(
            action_type=ActionType.FINAL_RESPONSE,
            reasoning="Unable to recover from errors",
            confidence=0.5,
            should_continue=False,
            final_response=self._generate_error_response(state)
        )
    
    def _create_final_response_action(self, state: ConversationState, 
                                    decision: ContinuationDecision) -> ActionDecision:
        """Create final response action based on continuation decision."""
        return ActionDecision(
            action_type=ActionType.FINAL_RESPONSE,
            reasoning=decision.reasoning,
            confidence=decision.confidence,
            should_continue=False,
            final_response=decision.final_response or self._generate_final_response(state)
        )
    
    # Helper methods
    def _format_tool_descriptions(self) -> str:
        """Format tool descriptions for LLM consumption."""
        tools = self.tool_registry.get_all_tool_descriptions()
        return json.dumps(tools, indent=2)
    
    def _format_conversation_history(self, history: List[Dict[str, Any]]) -> str:
        """Format conversation history as readable text."""
        if not history:
            return "No previous interactions."
        
        formatted = []
        for entry in history:
            formatted.append(f"Iteration {entry['iteration']}:")
            formatted.append(f"  Reasoning: {entry['reasoning']}")
            formatted.append(f"  Tools used: {', '.join(entry['tool_calls'])}")
            formatted.append(f"  Results: {entry['results_summary']}")
        
        return "\n".join(formatted)
    
    def _format_tool_results(self, results: List[Dict[str, Any]]) -> str:
        """Format tool results for LLM consumption."""
        formatted = []
        for result in results:
            if result["status"] == "success":
                formatted.append(f"{result['tool_name']}: {result['result']}")
            else:
                formatted.append(f"{result['tool_name']}: ERROR - {result['error']}")
        
        return "\n".join(formatted)
```

### 4. ActivityManager Implementation

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
import uuid

class ActivityManager:
    """External controller for ManualAgentLoop with full execution control."""
    
    def __init__(self, agent_loop: ManualAgentLoop, tool_registry,
                 max_iterations: int = 10, 
                 execution_mode: str = "sequential"):
        self.agent_loop = agent_loop
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations
        self.execution_mode = execution_mode  # "sequential", "parallel", "selective"
        
        # Execution control
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.activity_cache = {}
        
    def run_activity(self, user_query: str, activity_id: str = None) -> Dict[str, Any]:
        """Run a complete activity with full control over execution."""
        activity_id = activity_id or str(uuid.uuid4())
        
        # Initialize conversation state
        state = ConversationState(
            user_query=user_query,
            activity_id=activity_id,
            max_iterations=self.max_iterations,
            start_time=time.time()
        )
        
        # Main execution loop
        while state.iteration_count < self.max_iterations:
            state.iteration_count += 1
            
            # Get next action from agent
            action = self.agent_loop.get_next_action(state)
            
            # Log decision
            self._log_action(activity_id, state.iteration_count, action)
            
            # Handle different action types
            if action.action_type == ActionType.TOOL_EXECUTION:
                # Execute tools based on execution mode
                tool_results = self._execute_tools(
                    action.tool_suggestions,
                    mode=self.execution_mode,
                    parallel_safe=action.parallel_safe
                )
                
                # Update state with results
                state.last_tool_results = tool_results
                state.total_tool_calls += len(tool_results)
                
                # Add to conversation history
                state.conversation_history.append({
                    "iteration": state.iteration_count,
                    "action": action.dict(),
                    "tool_results": tool_results,
                    "timestamp": time.time()
                })
                
            elif action.action_type == ActionType.FINAL_RESPONSE:
                # Activity complete
                return self._create_activity_result(
                    activity_id, state, action.final_response
                )
                
            elif action.action_type == ActionType.ERROR_RECOVERY:
                # Handle error recovery
                if not action.should_continue:
                    return self._create_activity_result(
                        activity_id, state, action.final_response, 
                        status="error_recovery"
                    )
            
            # Check for manual termination conditions
            if self._should_terminate(state, action):
                final_response = self._generate_termination_response(state)
                return self._create_activity_result(
                    activity_id, state, final_response, 
                    status="terminated"
                )
        
        # Max iterations reached
        timeout_response = self._generate_timeout_response(state)
        return self._create_activity_result(
            activity_id, state, timeout_response, 
            status="max_iterations"
        )

    def _execute_tools(self, tool_calls: List[ToolCall], 
                      mode: str = "sequential", 
                      parallel_safe: bool = True) -> List[Dict[str, Any]]:
        """Execute tools with specified execution mode."""
        
        if mode == "parallel" and parallel_safe and len(tool_calls) > 1:
            return self._execute_parallel(tool_calls)
        elif mode == "selective":
            return self._execute_selective(tool_calls)
        else:
            return self._execute_sequential(tool_calls)
    
    def _execute_sequential(self, tool_calls: List[ToolCall]) -> List[Dict[str, Any]]:
        """Execute tools one at a time."""
        results = []
        
        for tool_call in tool_calls:
            try:
                # Get tool function
                tool_func = self.tool_registry.get_function(tool_call.tool_name)
                
                # Execute with timing
                start_time = time.time()
                result = tool_func(**tool_call.parameters)
                execution_time = time.time() - start_time
                
                results.append({
                    "tool_name": tool_call.tool_name,
                    "status": "success",
                    "result": result,
                    "execution_time": execution_time,
                    "parameters": tool_call.parameters
                })
                
            except Exception as e:
                results.append({
                    "tool_name": tool_call.tool_name,
                    "status": "error",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "parameters": tool_call.parameters
                })
        
        return results
    
    def _execute_parallel(self, tool_calls: List[ToolCall]) -> List[Dict[str, Any]]:
        """Execute tools in parallel."""
        futures = {}
        results = []
        
        # Submit all tools
        for tool_call in tool_calls:
            future = self.executor.submit(
                self._execute_single_tool, tool_call
            )
            futures[future] = tool_call
        
        # Collect results
        for future in as_completed(futures, timeout=30):
            tool_call = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({
                    "tool_name": tool_call.tool_name,
                    "status": "error",
                    "error": str(e),
                    "error_type": "ExecutionError"
                })
        
        return results
    
    def _execute_selective(self, tool_calls: List[ToolCall]) -> List[Dict[str, Any]]:
        """Execute tools with custom logic (e.g., prioritization, conditional)."""
        results = []
        
        # Sort by priority (example: certain tools first)
        priority_order = ["search", "calculate", "analyze"]
        sorted_calls = sorted(
            tool_calls,
            key=lambda x: priority_order.index(x.tool_name) 
                         if x.tool_name in priority_order else 999
        )
        
        for tool_call in sorted_calls:
            result = self._execute_single_tool(tool_call)
            results.append(result)
            
            # Conditional execution based on results
            if result["status"] == "success" and tool_call.tool_name == "search":
                # If search found results, maybe skip alternative searches
                remaining_searches = [
                    tc for tc in tool_calls 
                    if tc.tool_name.endswith("_search") and tc != tool_call
                ]
                if remaining_searches and "found" in str(result.get("result", "")):
                    for skip_call in remaining_searches:
                        results.append({
                            "tool_name": skip_call.tool_name,
                            "status": "skipped",
                            "reason": "Primary search already found results"
                        })
        
        return results
```

## Key Implementation Details

### 5. Tool Registry Integration

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class ToolRegistry(Protocol):
    """Protocol for tool registry compatibility."""
    
    def get_tool(self, tool_name: str) -> callable:
        """Get a tool function by name."""
        ...
    
    def get_all_tool_names(self) -> List[str]:
        """Get all registered tool names."""
        ...
    
    def get_all_tool_descriptions(self) -> List[Dict[str, Any]]:
        """Get tool descriptions in standardized format."""
        ...

class DSPyToolRegistryAdapter:
    """Adapter to make existing tool registries work with the agent loop."""
    
    def __init__(self, existing_registry):
        self.registry = existing_registry
    
    def get_tool(self, tool_name: str) -> callable:
        """Get tool with error handling."""
        try:
            return self.registry.get_function(tool_name)
        except KeyError:
            raise ValueError(f"Tool '{tool_name}' not found in registry")
    
    def get_all_tool_names(self) -> List[str]:
        """Get tool names."""
        return list(self.registry._functions.keys())
    
    def get_all_tool_descriptions(self) -> List[Dict[str, Any]]:
        """Convert tool definitions to standardized format."""
        descriptions = []
        for tool_def in self.registry.get_tool_definitions():
            desc = {
                "name": tool_def.name.value,
                "description": tool_def.description,
                "parameters": []
            }
            
            if tool_def.arguments:
                for arg in tool_def.arguments:
                    desc["parameters"].append({
                        "name": arg.name,
                        "type": arg.type,
                        "description": arg.description,
                        "required": arg.required
                    })
            
            descriptions.append(desc)
        
        return descriptions
```

### 6. Conversation History Management

```python
class ConversationEntry(BaseModel):
    """Single entry in conversation history."""
    iteration: int
    timestamp: float
    reasoning: str
    tool_calls: List[str]
    tool_parameters: Dict[str, Dict[str, Any]]
    results: List[Dict[str, Any]]
    results_summary: str
    errors: List[str] = Field(default_factory=list)

class ConversationManager:
    """Manages conversation history with summarization and retrieval."""
    
    def __init__(self, max_history_length: int = 10):
        self.max_history_length = max_history_length
        self.history: List[ConversationEntry] = []
        
        # DSPy module for summarization
        self.summarizer = dspy.ChainOfThought(
            "conversation_entries -> summary, key_findings, unresolved_questions"
        )
    
    def add_entry(self, entry: ConversationEntry):
        """Add entry and manage history length."""
        self.history.append(entry)
        
        # Summarize old entries if history is too long
        if len(self.history) > self.max_history_length:
            self._compress_history()
    
    def _compress_history(self):
        """Compress old history entries into summary."""
        # Take first half of history to summarize
        to_summarize = self.history[:len(self.history)//2]
        
        # Create summary
        summary_text = self._format_entries_for_summary(to_summarize)
        summary_result = self.summarizer(conversation_entries=summary_text)
        
        # Create summary entry
        summary_entry = ConversationEntry(
            iteration=-1,  # Special marker for summaries
            timestamp=to_summarize[0].timestamp,
            reasoning=f"SUMMARY: {summary_result.summary}",
            tool_calls=["<summarized>"],
            tool_parameters={},
            results=[{"summary": summary_result.key_findings}],
            results_summary=summary_result.summary
        )
        
        # Replace old entries with summary
        self.history = [summary_entry] + self.history[len(self.history)//2:]
    
    def get_formatted_history(self, last_n: int = None) -> str:
        """Get formatted history for LLM consumption."""
        entries = self.history[-last_n:] if last_n else self.history
        
        formatted = []
        for entry in entries:
            if entry.iteration == -1:  # Summary entry
                formatted.append(f"[Previous Summary]: {entry.reasoning}")
            else:
                formatted.append(f"Iteration {entry.iteration}:")
                formatted.append(f"  Reasoning: {entry.reasoning}")
                formatted.append(f"  Tools: {', '.join(entry.tool_calls)}")
                formatted.append(f"  Results: {entry.results_summary}")
                if entry.errors:
                    formatted.append(f"  Errors: {', '.join(entry.errors)}")
        
        return "\n\n".join(formatted)
```

### 7. Advanced Error Handling

```python
class ErrorRecoveryStrategy(BaseModel):
    """Strategy for recovering from tool errors."""
    strategy_type: Literal["retry", "alternative_tool", "skip", "fail"]
    details: str
    alternative_tool: Optional[str] = None
    retry_with_params: Optional[Dict[str, Any]] = None

class ErrorHandler(dspy.Module):
    """Advanced error handling with recovery strategies."""
    
    def __init__(self):
        super().__init__()
        
        # Signature for error analysis
        class ErrorAnalysisSignature(dspy.Signature):
            """Analyze error and suggest recovery strategy."""
            error_message: str = dspy.InputField(desc="The error message")
            error_type: str = dspy.InputField(desc="Type of error (e.g., ValueError)")
            failed_tool: str = dspy.InputField(desc="Name of the tool that failed")
            tool_parameters: str = dspy.InputField(desc="Parameters that caused the error")
            user_query: str = dspy.InputField(desc="Original user request")
            available_tools: str = dspy.InputField(desc="List of available tools")
            
            recovery: ErrorRecoveryStrategy = dspy.OutputField(desc="Recovery strategy")
        
        self.analyzer = dspy.ChainOfThought(ErrorAnalysisSignature)
    
    def forward(self, error_info: Dict[str, Any], user_query: str, 
                available_tools: List[str]) -> ErrorRecoveryStrategy:
        """Analyze error and suggest recovery."""
        
        result = self.analyzer(
            error_message=str(error_info["error"]),
            error_type=error_info.get("error_type", "Unknown"),
            failed_tool=error_info["tool_name"],
            tool_parameters=json.dumps(error_info.get("parameters", {})),
            user_query=user_query,
            available_tools=json.dumps(available_tools)
        )
        
        return result.recovery
    
    def apply_recovery(self, strategy: ErrorRecoveryStrategy, 
                      original_call: ToolCall) -> Optional[ToolCall]:
        """Apply recovery strategy to create new tool call."""
        
        if strategy.strategy_type == "retry":
            # Retry with modified parameters
            new_call = ToolCall(
                tool_name=original_call.tool_name,
                parameters=strategy.retry_with_params or original_call.parameters,
                reasoning=f"Retrying after error: {strategy.details}"
            )
            return new_call
        
        elif strategy.strategy_type == "alternative_tool":
            # Use alternative tool
            if strategy.alternative_tool:
                new_call = ToolCall(
                    tool_name=strategy.alternative_tool,
                    parameters=original_call.parameters,  # May need adjustment
                    reasoning=f"Using alternative tool: {strategy.details}"
                )
                return new_call
        
        # For "skip" or "fail", return None
        return None
```

### 8. Performance Optimizations

```python
class CachedToolExecutor:
    """Tool executor with caching for repeated calls."""
    
    def __init__(self, cache_size: int = 100):
        self.cache = {}
        self.cache_order = []
        self.cache_size = cache_size
    
    def _get_cache_key(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Generate cache key from tool call."""
        # Sort parameters for consistent keys
        param_str = json.dumps(parameters, sort_keys=True)
        return f"{tool_name}:{hashlib.md5(param_str.encode()).hexdigest()}"
    
    def execute_with_cache(self, tool_func: callable, tool_name: str, 
                          parameters: Dict[str, Any]) -> Any:
        """Execute tool with caching."""
        cache_key = self._get_cache_key(tool_name, parameters)
        
        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Execute tool
        result = tool_func(**parameters)
        
        # Update cache
        self.cache[cache_key] = result
        self.cache_order.append(cache_key)
        
        # Evict old entries if needed
        if len(self.cache_order) > self.cache_size:
            old_key = self.cache_order.pop(0)
            del self.cache[old_key]
        
        return result

class BatchToolSelector(dspy.Module):
    """Optimized tool selector that can suggest multiple iterations at once."""
    
    def __init__(self):
        super().__init__()
        
        class BatchSelectionSignature(dspy.Signature):
            """Plan multiple tool calls across iterations."""
            user_query: str = dspy.InputField()
            available_tools: str = dspy.InputField()
            
            plan: str = dspy.OutputField(desc="Multi-step plan")
            iterations: List[ToolSelectionOutput] = dspy.OutputField(
                desc="Tool selections for multiple iterations"
            )
        
        self.planner = dspy.ChainOfThought(BatchSelectionSignature)
```

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

## Implementation Examples

### Example 1: Basic ActivityManager Usage

```python
# Initialize components
registry = MultiToolRegistry()
registry.register(search_web, calculate, get_weather)

# Create agent and activity manager
agent = ManualAgentLoop(
    tool_registry=DSPyToolRegistryAdapter(registry),
    enable_error_recovery=True
)

activity_manager = ActivityManager(
    agent_loop=agent,
    tool_registry=registry,
    max_iterations=5,
    execution_mode="sequential"
)

# Run activity
result = activity_manager.run_activity(
    "What's the weather in Paris and how much is 100 EUR in USD?"
)

print(f"Final response: {result['final_response']}")
print(f"Total iterations: {result['iterations']}")
print(f"Tools used: {result['tools_used']}")
```

### Example 2: Advanced Execution Control

```python
class CustomActivityManager(ActivityManager):
    """Extended ActivityManager with custom execution logic."""
    
    def _should_terminate(self, state: ConversationState, 
                         action: ActionDecision) -> bool:
        """Custom termination logic."""
        # Terminate if confidence is too low
        if action.confidence < 0.3:
            return True
        
        # Terminate if too many errors
        if len(state.errors_encountered) > 3:
            return True
        
        # Terminate if specific tools fail
        critical_tools = ["payment_process", "order_submit"]
        if state.last_tool_results:
            for result in state.last_tool_results:
                if (result.get("tool_name") in critical_tools and 
                    result.get("status") == "error"):
                    return True
        
        return False
    
    def _execute_tools_with_validation(self, tool_calls: List[ToolCall]) -> List[Dict[str, Any]]:
        """Execute tools with pre-validation."""
        validated_calls = []
        
        for tool_call in tool_calls:
            # Validate parameters before execution
            if self._validate_tool_call(tool_call):
                validated_calls.append(tool_call)
            else:
                # Log validation failure
                self._log_validation_failure(tool_call)
        
        # Execute validated tools
        return self._execute_tools(validated_calls, mode=self.execution_mode)

# Use custom manager
custom_manager = CustomActivityManager(
    agent_loop=agent,
    tool_registry=registry,
    max_iterations=10,
    execution_mode="selective"
)

result = custom_manager.run_activity(
    "Process order #12345 and send confirmation email"
)
```

### Example 3: Async ActivityManager

```python
class AsyncActivityManager(ActivityManager):
    """ActivityManager with async execution support."""
    
    async def run_activity_async(self, user_query: str) -> Dict[str, Any]:
        """Run activity with async tool execution."""
        state = ConversationState(
            user_query=user_query,
            activity_id=str(uuid.uuid4()),
            start_time=time.time()
        )
        
        while state.iteration_count < self.max_iterations:
            state.iteration_count += 1
            
            # Get action synchronously (DSPy is sync)
            action = await asyncio.to_thread(
                self.agent_loop.get_next_action, state
            )
            
            if action.action_type == ActionType.TOOL_EXECUTION:
                # Execute tools asynchronously
                tool_results = await self._execute_tools_async(
                    action.tool_suggestions
                )
                
                state.last_tool_results = tool_results
                state.conversation_history.append({
                    "iteration": state.iteration_count,
                    "action": action.dict(),
                    "tool_results": tool_results
                })
                
            elif action.action_type == ActionType.FINAL_RESPONSE:
                return self._create_activity_result(
                    state.activity_id, state, action.final_response
                )
        
        return self._create_activity_result(
            state.activity_id, state, 
            "Max iterations reached", 
            status="timeout"
        )
    
    async def _execute_tools_async(self, tool_calls: List[ToolCall]) -> List[Dict[str, Any]]:
        """Execute tools asynchronously."""
        tasks = []
        
        for tool_call in tool_calls:
            task = asyncio.create_task(
                self._execute_tool_async(tool_call)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        formatted_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                formatted_results.append({
                    "tool_name": tool_calls[i].tool_name,
                    "status": "error",
                    "error": str(result)
                })
            else:
                formatted_results.append(result)
        
        return formatted_results

# Use async manager
async def main():
    async_manager = AsyncActivityManager(
        agent_loop=agent,
        tool_registry=registry
    )
    
    result = await async_manager.run_activity_async(
        "Search for flights and hotels in parallel"
    )
    
    print(result)

# Run
asyncio.run(main())
```

### Example 4: Monitoring and Observability

```python
class ObservableActivityManager(ActivityManager):
    """ActivityManager with built-in monitoring."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metrics = {
            "total_activities": 0,
            "successful_activities": 0,
            "failed_activities": 0,
            "total_tool_calls": 0,
            "tool_errors": 0,
            "average_iterations": 0
        }
        self.activity_logs = []
    
    def run_activity(self, user_query: str, **kwargs) -> Dict[str, Any]:
        """Run activity with monitoring."""
        self.metrics["total_activities"] += 1
        
        # Create activity log entry
        log_entry = {
            "activity_id": kwargs.get("activity_id", str(uuid.uuid4())),
            "start_time": time.time(),
            "user_query": user_query,
            "events": []
        }
        
        try:
            # Override action logging
            original_log = self._log_action
            self._log_action = lambda aid, iter, action: log_entry["events"].append({
                "type": "action",
                "iteration": iter,
                "action": action.dict(),
                "timestamp": time.time()
            })
            
            # Run activity
            result = super().run_activity(user_query, **kwargs)
            
            # Update metrics
            self.metrics["successful_activities"] += 1
            self.metrics["total_tool_calls"] += result.get("total_tool_calls", 0)
            
            # Update average iterations
            total = self.metrics["total_activities"]
            avg = self.metrics["average_iterations"]
            self.metrics["average_iterations"] = (
                (avg * (total - 1) + result["iterations"]) / total
            )
            
            log_entry["status"] = "success"
            log_entry["end_time"] = time.time()
            log_entry["duration"] = log_entry["end_time"] - log_entry["start_time"]
            
        except Exception as e:
            self.metrics["failed_activities"] += 1
            log_entry["status"] = "failed"
            log_entry["error"] = str(e)
            result = {"error": str(e), "status": "failed"}
        
        finally:
            self.activity_logs.append(log_entry)
            self._log_action = original_log
        
        return result
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary."""
        return {
            **self.metrics,
            "success_rate": (
                self.metrics["successful_activities"] / 
                max(1, self.metrics["total_activities"])
            ),
            "error_rate": (
                self.metrics["tool_errors"] / 
                max(1, self.metrics["total_tool_calls"])
            )
        }
```

## Testing Strategy

```python
import pytest
from unittest.mock import Mock, patch

class TestManualAgentLoop:
    """Comprehensive test suite for agent loop."""
    
    @pytest.fixture
    def mock_registry(self):
        """Create mock tool registry."""
        registry = Mock()
        registry.get_all_tool_names.return_value = ["search", "calculate"]
        registry.get_all_tool_descriptions.return_value = [
            {"name": "search", "description": "Search the web"},
            {"name": "calculate", "description": "Perform calculations"}
        ]
        return registry
    
    def test_single_iteration_success(self, mock_registry):
        """Test successful single iteration."""
        agent = ManualAgentLoop(mock_registry, max_iterations=1)
        
        # Mock tool selection
        with patch.object(agent.tool_selector, 'forward') as mock_select:
            mock_select.return_value.output = ToolSelectionOutput(
                reasoning="Need to search for information",
                tool_calls=[ToolCall(
                    tool_name="search",
                    parameters={"query": "test"},
                    reasoning="Search for test"
                )],
                parallel_execution=False
            )
            
            # Mock continuation decision
            with patch.object(agent.continuation_decider, 'forward') as mock_decide:
                mock_decide.return_value.decision = ContinuationDecision(
                    should_continue=False,
                    confidence=0.9,
                    reasoning="Found the answer",
                    final_response="Here is your answer"
                )
                
                # Run agent
                state = agent("test query")
                
                assert state.final_response == "Here is your answer"
                assert state.iteration_count == 1
                assert state.total_tool_calls == 1
    
    def test_error_recovery(self, mock_registry):
        """Test error handling and recovery."""
        # Test implementation...
        pass
    
    def test_parallel_execution(self, mock_registry):
        """Test parallel tool execution."""
        # Test implementation...
        pass
```

## Next Steps

1. **Implementation Priority**:
   - Core loop structure with basic tool selection
   - Error handling and recovery
   - Conversation history management
   - Performance optimizations

2. **Integration Points**:
   - Adapt existing MultiToolRegistry
   - Connect to current tool implementations
   - Add monitoring and logging

3. **Optimization**:
   - Collect real usage examples
   - Train with DSPy teleprompters
   - Fine-tune prompts and decision logic

4. **Production Readiness**:
   - Comprehensive test suite
   - Performance benchmarks
   - Documentation and examples

## Suggested Improvements

The architecture described above is comprehensive but also introduces significant complexity by separating tool selection, continuation decisions, and error handling into distinct DSPy modules. A more streamlined and DSPy-native approach would be to unify these reasoning steps into a single, more powerful module.

This aligns with the "glass-box" agent pattern, where the external loop is simple, and the complex reasoning is encapsulated within one optimizable DSPy module.

### 1. Unify Reasoning into a Single Module

Instead of chaining `ToolSelector`, `ContinuationDecider`, and `ErrorHandler`, create a single `AgentReasoner` module that performs the entire reasoning step at once.

**A. Define a Unified Signature:**

Create a single signature that takes the full context and decides on the next complete action.

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Union

class ToolCall(BaseModel):
    tool_name: str
    parameters: dict
    reasoning: str

class FinalAnswer(BaseModel):
    answer: str
    reasoning: str

class ActionDecision(BaseModel):
    """A union type for the agent's decision."""
    action: Union[ToolCall, FinalAnswer]

class AgentSignature(dspy.Signature):
    """
    Given the user's query and the history of previous actions, decide on the next tool to call or provide the final answer.
    """
    question = dspy.InputField(desc="The user's original question.")
    history = dspy.InputField(desc="The history of previous tool calls and observations, including errors.")
    available_tools = dspy.InputField(desc="A list of available tools and their descriptions.")

    decision = dspy.OutputField(desc="The next action to take, as a JSON object representing a ToolCall or FinalAnswer.")

```

**B. Create a Simplified Reasoner Module:**

The `ManualAgentLoop` can be replaced by a much simpler `AgentReasoner` module.

```python
class AgentReasoner(dspy.Module):
    """A unified module that determines the next agent action."""
    def __init__(self, tool_names: List[str]):
        super().__init__()
        # This Predict module does all the heavy lifting.
        # It can be replaced with ChainOfThought or a custom class.
        self.generate_action = dspy.Predict(AgentSignature)
        self.tool_names = tool_names # For reference if needed

    def forward(self, question: str, history: str, available_tools: str):
        # The entire reasoning step is a single call to the LM.
        return self.generate_action(
            question=question,
            history=history,
            available_tools=available_tools
        )
```

### 2. Simplify State and History Management

The complex `ConversationState` and `ConversationManager` objects can be replaced with a simple, formatted string for the history. The external `ActivityManager` is responsible for maintaining this string. This is more aligned with how DSPy examples are structured and is easier to debug.

**Simplified History String:**

```
Thought: The user wants to know the weather in Paris. I should use the `get_weather` tool.
Action: get_weather(city="Paris")
Observation: The weather in Paris is 22°C and sunny.

Thought: The user also wants to know the conversion from EUR to USD. I should use the `currency_converter` tool.
Action: currency_converter(from="EUR", to="USD", amount=100)
Observation: 100 EUR is approximately 108 USD.

Thought: I have answered both parts of the user's question. I can now provide the final answer.
Action: FinalAnswer("The weather in Paris is 22°C and sunny, and 100 EUR is about 108 USD.")
```

### 3. Streamline the External `ActivityManager`

With a unified reasoner, the `ActivityManager` becomes much simpler. Its primary job is to call the reasoner, execute the resulting action, and append the results to the history string.

```python
class SimplifiedActivityManager:
    def __init__(self, reasoner: AgentReasoner, tool_registry):
        self.reasoner = reasoner
        self.tool_registry = tool_registry

    def run_activity(self, question: str, max_steps: int = 5):
        history = ""
        available_tools = json.dumps(self.tool_registry.get_all_tool_descriptions(), indent=2)

        for i in range(max_steps):
            # 1. Call the unified reasoner
            prediction = self.reasoner(question=question, history=history, available_tools=available_tools)
            
            # Assumes the output can be parsed into the ActionDecision Pydantic model
            decision = ActionDecision.parse_raw(prediction.decision)

            # 2. Execute the action
            if isinstance(decision.action, FinalAnswer):
                print(f"Final Answer: {decision.action.answer}")
                return decision.action.answer

            elif isinstance(decision.action, ToolCall):
                tool_call = decision.action
                print(f"Tool Call: {tool_call.tool_name}({tool_call.parameters})")
                
                try:
                    observation = self.tool_registry.execute(tool_call.tool_name, tool_call.parameters)
                except Exception as e:
                    observation = f"Error executing tool: {str(e)}"

                print(f"Observation: {observation}")

                # 3. Append to history and loop
                history += f"\nThought: {tool_call.reasoning}\nAction: {tool_call.tool_name}({json.dumps(tool_call.parameters)})\nObservation: {observation}"
        
        return "Agent stopped due to max steps."
```

### 4. Advantages of the Simplified Approach

1.  **Easier Optimization**: Optimizing a single `AgentReasoner` module is much more straightforward. You can create `dspy.Example` traces that show the full `(question, history) -> decision` transformation and use a teleprompter like `BootstrapFewShot` to compile the module directly.
2.  **Reduced Complexity**: The number of classes and the amount of "glue code" are significantly reduced, making the system easier to understand, maintain, and debug.
3.  **Closer to DSPy Philosophy**: This design treats the LLM as a programmable reasoner (`dspy.Predict`) and keeps the control flow in standard Python, which is a core principle of DSPy.
4.  **Improved Robustness**: A single, well-prompted module is often more robust than a chain of smaller modules, as it can consider all aspects of the problem (continuation, error handling, tool selection) holistically in one step.