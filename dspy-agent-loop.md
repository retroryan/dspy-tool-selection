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

```python
class ErrorRecoveryStrategy(BaseModel):
    """Strategy for recovering from tool errors."""
    strategy_type: Literal["retry", "alternative_tool", "skip", "fail"]
    details: str
    alternative_tool: Optional[str] = None
    retry_with_params: Optional[Dict[str, Any]] = None
    can_recover: bool = Field(default=True)

class ErrorRecoverySignature(dspy.Signature):
    """Analyze error and suggest recovery strategy."""
    
    error_message: str = dspy.InputField(desc="The error message from failed tool")
    error_type: str = dspy.InputField(desc="Type of error (e.g., ValueError)")
    failed_tool: str = dspy.InputField(desc="Name of the tool that failed")
    tool_parameters: str = dspy.InputField(desc="Parameters that caused the error")
    user_query: str = dspy.InputField(desc="Original user request for context")
    available_tools: str = dspy.InputField(desc="List of available alternative tools")
    previous_attempts: str = dspy.InputField(desc="History of previous recovery attempts")
    
    recovery_strategy: ErrorRecoveryStrategy = dspy.OutputField(desc="Recommended recovery approach")

class ErrorRecoveryModule(dspy.Module):
    """Specialized module for error recovery strategies."""
    
    def __init__(self, recovery_strategies: List[str] = None):
        super().__init__()
        self.strategies = recovery_strategies or ["retry", "alternative_tool", "graceful_degradation"]
        self.recovery_planner = dspy.ChainOfThought(ErrorRecoverySignature)
    
    def forward(self, error_info: Dict[str, Any], context: ConversationState,
                available_tools: List[str]) -> ErrorRecoveryStrategy:
        """Generate recovery strategy for tool errors."""
        
        # Format previous attempts
        previous_attempts = self._format_previous_attempts(context.errors_encountered)
        
        result = self.recovery_planner(
            error_message=str(error_info.get("error", "")),
            error_type=error_info.get("error_type", "Unknown"),
            failed_tool=error_info.get("tool_name", ""),
            tool_parameters=json.dumps(error_info.get("parameters", {})),
            user_query=context.user_query,
            available_tools=json.dumps(available_tools),
            previous_attempts=previous_attempts
        )
        
        return result.recovery_strategy
```

### 3. Response Formatting Module (Optional)

```python
class ResponseFormatter(dspy.Module):
    """Format final responses based on context and style requirements."""
    
    def __init__(self, style_guide: str = "concise", include_confidence: bool = False):
        super().__init__()
        self.style_guide = style_guide
        self.include_confidence = include_confidence
        
        # Different formatters for different styles
        if style_guide == "detailed":
            self.formatter = dspy.ChainOfThought(
                "raw_response, user_query, key_results, tool_history -> formatted_response, summary_points"
            )
        else:
            self.formatter = dspy.Predict(
                "raw_response, user_query, key_results -> formatted_response"
            )
    
    def forward(self, raw_response: str, user_query: str, 
                state: ConversationState) -> str:
        """Format response based on style guide."""
        
        # Extract key results from conversation history
        key_results = self._extract_key_results(state.conversation_history)
        
        if self.style_guide == "detailed":
            result = self.formatter(
                raw_response=raw_response,
                user_query=user_query,
                key_results=json.dumps(key_results),
                tool_history=self._format_tool_history(state.conversation_history)
            )
            
            formatted = f"{result.formatted_response}\n\n"
            if hasattr(result, 'summary_points'):
                formatted += "Key Points:\n"
                for point in result.summary_points:
                    formatted += f"• {point}\n"
                    
            if self.include_confidence and state.last_confidence:
                formatted += f"\nConfidence: {state.last_confidence:.0%}"
                
            return formatted
        else:
            result = self.formatter(
                raw_response=raw_response,
                user_query=user_query,
                key_results=json.dumps(key_results)
            )
            return result.formatted_response
```

### 4. Stateless Agent Loop for External Control

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
    """Stateless agent loop designed for external control by ActivityManager.
    
    Uses a hybrid approach with consolidated reasoning for tool selection and
    continuation decisions, while keeping error recovery and formatting separate.
    """
    
    def __init__(self, tool_registry, enable_error_recovery: bool = True,
                 response_style: str = "concise"):
        super().__init__()
        self.tool_registry = tool_registry
        self.enable_error_recovery = enable_error_recovery
        
        # Core reasoning module (hybrid approach)
        tool_names = list(tool_registry.get_all_tool_names())
        self.agent_reasoner = AgentReasoner(
            tool_names=tool_names,
            max_iterations=10  # Default max, can be overridden by ActivityManager
        )
        
        # Specialized modules (kept separate for flexibility)
        if enable_error_recovery:
            self.error_recovery = ErrorRecoveryModule()
        
        # Optional response formatter
        self.response_formatter = ResponseFormatter(
            style_guide=response_style,
            include_confidence=True
        )
    
    def get_next_action(self, state: ConversationState) -> ActionDecision:
        """Get next action suggestion based on current state.
        
        This is the main entry point for ActivityManager to interact with the agent.
        Each call is stateless - all context is provided in the state parameter.
        """
        start_time = time.time()
        
        try:
            # Handle errors from previous tool execution if any
            if state.last_tool_results and any(r.get("status") == "error" for r in state.last_tool_results):
                if self.enable_error_recovery:
                    return self._handle_tool_errors(state)
                # Without error recovery, continue to main reasoning
            
            # Main reasoning - unified tool selection and continuation decision
            reasoning_result = self._perform_core_reasoning(state)
            reasoning_output = reasoning_result.reasoning_output
            
            # Store confidence for potential formatting
            state.last_confidence = reasoning_output.confidence
            
            # Convert reasoning output to action decision
            if not reasoning_output.should_continue:
                # Generate final response
                final_response = reasoning_output.final_response
                if final_response and self.response_formatter:
                    final_response = self.response_formatter(
                        raw_response=final_response,
                        user_query=state.user_query,
                        state=state
                    )
                
                return ActionDecision(
                    action_type=ActionType.FINAL_RESPONSE,
                    reasoning=reasoning_output.continuation_reasoning,
                    confidence=reasoning_output.confidence,
                    should_continue=False,
                    final_response=final_response,
                    processing_time=time.time() - start_time
                )
            
            elif reasoning_output.should_use_tools:
                # Return tool execution suggestion
                return ActionDecision(
                    action_type=ActionType.TOOL_EXECUTION,
                    reasoning=reasoning_output.overall_reasoning,
                    confidence=reasoning_output.confidence,
                    tool_suggestions=reasoning_output.tool_calls,
                    parallel_safe=reasoning_output.parallel_safe,
                    should_continue=True,
                    suggested_next_action=reasoning_output.suggested_next_action,
                    processing_time=time.time() - start_time
                )
            
            else:
                # Edge case: continue but no tools suggested
                return ActionDecision(
                    action_type=ActionType.TOOL_EXECUTION,
                    reasoning="Need more information but no specific tools identified",
                    confidence=0.5,
                    tool_suggestions=[],
                    should_continue=True,
                    processing_time=time.time() - start_time
                )
            
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
    
    def _perform_core_reasoning(self, state: ConversationState) -> dspy.Prediction:
        """Perform unified reasoning about tools and continuation."""
        # Format inputs for reasoning
        history = self._format_conversation_history(state.conversation_history)
        last_results = self._format_tool_results(state.last_tool_results) if state.last_tool_results else None
        available_tools = self._format_tool_descriptions()
        
        # Use the unified reasoner
        return self.agent_reasoner(
            user_query=state.user_query,
            conversation_history=history,
            last_tool_results=last_results,
            available_tools=available_tools,
            iteration_count=state.iteration_count
        )
    
    def _handle_tool_errors(self, state: ConversationState) -> ActionDecision:
        """Handle errors from previous tool execution using specialized error recovery module."""
        start_time = time.time()
        
        # Extract error information
        failed_tools = [r for r in state.last_tool_results if r.get("status") == "error"]
        
        if not failed_tools:
            # No actual errors, continue with normal reasoning
            return self.get_next_action(state)
        
        # Process each error through recovery module
        recovery_actions = []
        for error_info in failed_tools:
            recovery_strategy = self.error_recovery(
                error_info=error_info,
                context=state,
                available_tools=list(self.tool_registry.get_all_tool_names())
            )
            
            if recovery_strategy.can_recover:
                recovery_actions.append(recovery_strategy)
        
        # Determine best recovery approach
        if recovery_actions:
            # Prioritize alternative tool strategies
            alt_tool_strategies = [r for r in recovery_actions if r.strategy_type == "alternative_tool"]
            retry_strategies = [r for r in recovery_actions if r.strategy_type == "retry"]
            
            if alt_tool_strategies:
                # Create tool calls for alternatives
                tool_calls = []
                for strategy in alt_tool_strategies:
                    if strategy.alternative_tool:
                        tool_calls.append(ToolCall(
                            tool_name=strategy.alternative_tool,
                            parameters=strategy.retry_with_params or {},
                            reasoning=strategy.details
                        ))
                
                return ActionDecision(
                    action_type=ActionType.TOOL_EXECUTION,
                    reasoning="Attempting recovery with alternative tools",
                    confidence=0.7,
                    tool_suggestions=tool_calls,
                    parallel_safe=False,  # Recovery tools should run sequentially
                    should_continue=True,
                    processing_time=time.time() - start_time
                )
            
            elif retry_strategies:
                # Retry with modified parameters
                tool_calls = []
                for strategy in retry_strategies:
                    # Find original tool call info
                    original_error = next(e for e in failed_tools if any(r == strategy for r in recovery_actions))
                    tool_calls.append(ToolCall(
                        tool_name=original_error["tool_name"],
                        parameters=strategy.retry_with_params or original_error.get("parameters", {}),
                        reasoning=f"Retry: {strategy.details}"
                    ))
                
                return ActionDecision(
                    action_type=ActionType.TOOL_EXECUTION,
                    reasoning="Retrying failed tools with adjusted parameters",
                    confidence=0.6,
                    tool_suggestions=tool_calls,
                    parallel_safe=False,
                    should_continue=True,
                    processing_time=time.time() - start_time
                )
        
        # No recovery possible, generate graceful error response
        error_summary = self._summarize_errors(failed_tools)
        final_response = self._generate_error_aware_response(state, error_summary)
        
        if self.response_formatter:
            final_response = self.response_formatter(
                raw_response=final_response,
                user_query=state.user_query,
                state=state
            )
        
        return ActionDecision(
            action_type=ActionType.FINAL_RESPONSE,
            reasoning=f"Unable to recover from errors: {error_summary}",
            confidence=0.5,
            should_continue=False,
            final_response=final_response,
            processing_time=time.time() - start_time
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

