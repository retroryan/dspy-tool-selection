"""
Shared data models for tool selection and agentic loop implementation.

This module contains the combined Pydantic models used by both the tool selection
system and the agentic loop implementation, defining the structure for tool
invocations, decision outputs, and conversation state management.
"""

from typing import List, Dict, Any, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field
import time


# =============================================================================
# Core Tool Models (originally from tool_selection/models.py)
# =============================================================================

class ToolCall(BaseModel):
    """
    Represents a single invocation of a tool with its specified arguments.

    This model is used to structure the output of the tool selection process,
    indicating which tool should be called and with what parameters.
    """
    tool_name: str = Field(
        ..., 
        description="The unique name of the tool to be called (e.g., 'set_reminder')"
    )
    arguments: Dict[str, Any] = Field(
        default_factory=dict, 
        description="A dictionary of arguments to pass to the tool, where keys are argument names and values are their corresponding values."
    )


class MultiToolDecision(BaseModel):
    """
    Represents the comprehensive decision made by the tool selector.

    This model encapsulates the reasoning behind the tool selection and a list
    of one or more tool calls that should be executed to fulfill the user's request.
    """
    reasoning: str = Field(
        ..., 
        description="A detailed explanation or step-by-step thought process behind why the specific tools were selected and how they address the user's request."
    )
    tool_calls: List[ToolCall] = Field(
        ..., 
        description="A list of ToolCall objects, each representing a tool to be invoked. The order of tools in this list may or may not be significant depending on the 'execution_order_matters' flag in the signature."
    )


# =============================================================================
# Agentic Loop Models (originally from agentic_loop/models.py)
# =============================================================================

class ActionType(str, Enum):
    """Types of actions the agent can suggest."""
    TOOL_EXECUTION = "tool_execution"
    FINAL_RESPONSE = "final_response"
    ERROR_RECOVERY = "error_recovery"
    GOAL_CHECK = "goal_check"


class ReasoningOutput(BaseModel):
    """Unified reasoning output combining tool selection and continuation decisions."""
    
    # Overall reasoning
    overall_reasoning: str = Field(
        ..., 
        description="High-level reasoning about the current state and next steps"
    )
    confidence: float = Field(
        ..., 
        ge=0, 
        le=1, 
        description="Confidence in the decision (0-1)"
    )
    
    # Tool selection
    should_use_tools: bool = Field(
        ..., 
        description="Whether tools should be called in this iteration"
    )
    tool_calls: Optional[List[ToolCall]] = Field(
        None, 
        description="List of tools to execute if should_use_tools is True"
    )
    parallel_safe: bool = Field(
        default=True, 
        description="Whether suggested tools can be executed in parallel"
    )
    
    # Continuation decision
    should_continue: bool = Field(
        ..., 
        description="Whether to continue after this iteration"
    )
    continuation_reasoning: str = Field(
        ..., 
        description="Specific reasoning about whether to continue or stop"
    )
    
    # Final response (if not continuing)
    final_response: Optional[str] = Field(
        None, 
        description="Final response to user if not continuing"
    )
    suggested_next_action: Optional[str] = Field(
        None, 
        description="Hint about what might be needed next if continuing"
    )


class ActionDecision(BaseModel):
    """Decision returned by the agent for external execution control."""
    
    action_type: ActionType = Field(
        ..., 
        description="Type of action suggested by the agent"
    )
    reasoning: str = Field(
        ..., 
        description="Detailed reasoning behind the action decision"
    )
    
    # Tool execution
    tool_calls: List[ToolCall] = Field(
        default_factory=list, 
        description="Tools to execute if action_type is TOOL_EXECUTION"
    )
    
    # Continuation logic
    should_continue: bool = Field(
        default=True, 
        description="Whether the agent loop should continue"
    )
    continuation_reasoning: Optional[str] = Field(
        None, 
        description="Reasoning about whether to continue"
    )
    
    # Final response
    final_response: Optional[str] = Field(
        None, 
        description="Final response if action_type is FINAL_RESPONSE"
    )
    
    # Metadata
    confidence_score: float = Field(
        default=0.5, 
        ge=0, 
        le=1, 
        description="Confidence in the decision (0-1)"
    )
    iteration_count: int = Field(
        default=0, 
        description="Current iteration number"
    )
    max_iterations: int = Field(
        default=5, 
        description="Maximum allowed iterations"
    )
    processing_time: float = Field(
        default=0, 
        description="Time taken to process this decision"
    )
    tokens_used: Optional[int] = Field(
        None, 
        description="Number of tokens used in LLM calls"
    )


class ToolExecutionResult(BaseModel):
    """Result of executing a single tool."""
    
    tool_name: str = Field(
        ..., 
        description="Name of the tool that was executed"
    )
    success: bool = Field(
        default=True, 
        description="Whether the tool execution was successful"
    )
    result: Optional[Any] = Field(
        None, 
        description="Tool execution result if successful"
    )
    error: Optional[str] = Field(
        None, 
        description="Error message if execution failed"
    )
    error_type: Optional[str] = Field(
        None, 
        description="Type of error that occurred"
    )
    execution_time: float = Field(
        default=0, 
        description="Time taken to execute the tool"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Parameters passed to the tool"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage in conversation history."""
        return self.model_dump()


class ConversationEntry(BaseModel):
    """Single entry in conversation history."""
    
    iteration: int = Field(
        ..., 
        description="Iteration number for this entry"
    )
    user_input: str = Field(
        ..., 
        description="User input for this iteration"
    )
    response: str = Field(
        ..., 
        description="Agent response for this iteration"
    )
    tool_calls_made: List[ToolCall] = Field(
        default_factory=list, 
        description="Tools that were called in this iteration"
    )
    tool_results: List[ToolExecutionResult] = Field(
        default_factory=list, 
        description="Results from tool executions in this iteration"
    )
    timestamp: float = Field(
        default_factory=time.time, 
        description="Timestamp of this entry"
    )


class ConversationState(BaseModel):
    """Complete conversation state for stateless operation."""
    
    # Core state
    user_query: str = Field(
        ..., 
        description="The user's original request"
    )
    goal: Optional[str] = Field(
        None, 
        description="Optional explicit goal statement"
    )
    iteration_count: int = Field(
        default=0, 
        description="Current iteration number"
    )
    
    # History and results
    conversation_history: List[ConversationEntry] = Field(
        default_factory=list, 
        description="List of previous conversation entries"
    )
    last_tool_results: Optional[List[ToolExecutionResult]] = Field(
        None, 
        description="Results from the most recent tool executions"
    )
    total_tool_calls: int = Field(
        default=0, 
        description="Total number of tool calls made"
    )
    errors_encountered: List[str] = Field(
        default_factory=list, 
        description="List of errors encountered during execution"
    )
    
    # ActivityManager metadata
    activity_id: Optional[str] = Field(
        None, 
        description="Unique identifier for this activity"
    )
    max_iterations: Optional[int] = Field(
        None, 
        description="Maximum allowed iterations"
    )
    start_time: Optional[float] = Field(
        None, 
        description="Activity start timestamp"
    )
    last_confidence: Optional[float] = Field(
        None, 
        description="Confidence from the last decision"
    )
    
    # Tool set information
    tool_set_name: Optional[str] = Field(
        None, 
        description="Name of the currently loaded tool set"
    )
    
    def add_iteration_result(self, action: ActionDecision, tool_results: Optional[List[Dict[str, Any]]] = None):
        """Add the results of an iteration to the conversation history."""
        iteration_entry = {
            "iteration": self.iteration_count,
            "action": action.model_dump(),
            "tool_results": tool_results or [],
            "timestamp": time.time()
        }
        self.conversation_history.append(iteration_entry)
        
        if tool_results:
            self.last_tool_results = tool_results
            self.total_tool_calls += len(tool_results)
            
            # Track any errors
            for result in tool_results:
                if result.get("status") == "error":
                    self.errors_encountered.append(
                        f"Tool {result.get('tool_name', 'unknown')}: {result.get('error', 'Unknown error')}"
                    )
        
        self.last_confidence = action.confidence


class ErrorRecoveryStrategy(BaseModel):
    """Strategy for recovering from tool errors."""
    
    strategy_type: str = Field(
        ..., 
        description="Type of recovery strategy (retry, alternative_tool, skip, fail)"
    )
    details: str = Field(
        ..., 
        description="Detailed description of the recovery approach"
    )
    alternative_tool: Optional[str] = Field(
        None, 
        description="Alternative tool to use if strategy_type is alternative_tool"
    )
    retry_with_params: Optional[Dict[str, Any]] = Field(
        None, 
        description="Modified parameters for retry strategy"
    )
    can_recover: bool = Field(
        default=True, 
        description="Whether recovery is possible"
    )
    confidence: float = Field(
        default=0.5, 
        ge=0, 
        le=1, 
        description="Confidence in the recovery strategy"
    )


class ActivityResult(BaseModel):
    """Final result of an activity managed by ActivityManager."""
    
    activity_id: str = Field(
        ..., 
        description="Unique identifier for the activity"
    )
    status: str = Field(
        ..., 
        description="Final status (completed, error_recovery, terminated, max_iterations)"
    )
    final_response: str = Field(
        ..., 
        description="Final response to the user"
    )
    
    # Execution metrics
    total_iterations: int = Field(
        ..., 
        description="Total number of iterations performed"
    )
    total_tool_calls: int = Field(
        ..., 
        description="Total number of tool calls made"
    )
    execution_time: float = Field(
        ..., 
        description="Total execution time in seconds"
    )
    
    # Tool set information
    tool_set_name: str = Field(
        ..., 
        description="Name of the tool set used"
    )
    tools_used: List[str] = Field(
        default_factory=list, 
        description="List of unique tools that were used"
    )
    
    # Error information
    errors_encountered: List[str] = Field(
        default_factory=list, 
        description="List of errors encountered during execution"
    )
    
    # Conversation state
    conversation_state: ConversationState = Field(
        ..., 
        description="Final conversation state"
    )
    
    # Optional metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional metadata about the activity"
    )