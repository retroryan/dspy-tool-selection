"""
Activity Manager for external control of agentic loops.

This module provides the ActivityManager class that orchestrates the execution
of agentic loops with full external control over tool execution and iteration.
"""

from typing import List, Dict, Any, Optional, Callable
import time
import uuid
from shared.models import (
    ConversationState,
    ConversationEntry,
    ActionDecision,
    ActionType,
    ToolCall,
    ToolExecutionResult,
    ActivityResult
)
from shared.tool_set_registry import ToolSetRegistry
from agentic_loop.manual_agent_loop import ManualAgentLoop


class ActivityManager:
    """
    External controller for ManualAgentLoop with full execution control.
    
    This class provides complete control over the agent loop execution,
    including tool execution, iteration management, and result formatting.
    """
    
    def __init__(self, 
                 agent_loop: ManualAgentLoop,
                 tool_registry: ToolSetRegistry,
                 max_iterations: int = 5,
                 timeout_seconds: float = 30.0):
        """
        Initialize the ActivityManager.
        
        Args:
            agent_loop: The ManualAgentLoop instance to control
            tool_registry: The ToolSetRegistry instance for executing tools
            max_iterations: Maximum iterations per activity
            timeout_seconds: Maximum time allowed for an activity
        """
        self.agent_loop = agent_loop
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations
        self.timeout_seconds = timeout_seconds
    
    def run_activity(self, 
                    user_query: str,
                    goal: Optional[str] = None,
                    activity_id: Optional[str] = None) -> ActivityResult:
        """
        Main execution loop with iteration control.
        
        Args:
            user_query: The user's request
            goal: Optional explicit goal
            activity_id: Optional activity identifier
            
        Returns:
            ActivityResult with complete execution details
        """
        # Initialize activity
        activity_id = activity_id or str(uuid.uuid4())
        start_time = time.time()
        
        # Initialize conversation state
        conversation_state = ConversationState(
            user_query=user_query,
            goal=goal,
            conversation_history=[],
            last_tool_results=None,
            iteration_count=0,
            max_iterations=self.max_iterations,
            activity_id=activity_id,
            start_time=start_time,
            tool_set_name=None  # Will be set if available
        )
        
        # Track execution metrics
        total_tool_calls = 0
        tools_used = set()
        errors_encountered = []
        
        try:
            # Main iteration loop
            while conversation_state.iteration_count < self.max_iterations:
                # Check timeout
                if time.time() - start_time > self.timeout_seconds:
                    return self._create_timeout_result(
                        activity_id, conversation_state, total_tool_calls,
                        list(tools_used), errors_encountered, start_time
                    )
                
                # Increment iteration
                conversation_state.iteration_count += 1
                
                # Get next action from agent
                action_decision = self.agent_loop.get_next_action(conversation_state)
                
                # Handle different action types
                if action_decision.action_type == ActionType.FINAL_RESPONSE:
                    # Agent decided to stop
                    return self._create_success_result(
                        activity_id, conversation_state, action_decision,
                        total_tool_calls, list(tools_used), errors_encountered, start_time
                    )
                
                elif action_decision.action_type == ActionType.ERROR_RECOVERY:
                    # Agent encountered an error
                    error_msg = action_decision.reasoning
                    errors_encountered.append(error_msg)
                    
                    return self._create_error_result(
                        activity_id, conversation_state, error_msg,
                        total_tool_calls, list(tools_used), errors_encountered, start_time
                    )
                
                elif action_decision.action_type == ActionType.TOOL_EXECUTION:
                    # Execute tools sequentially
                    tool_results = self._execute_tools_sequential(action_decision.tool_calls)
                    
                    # Update metrics
                    total_tool_calls += len(tool_results)
                    for result in tool_results:
                        tools_used.add(result.tool_name)
                        if not result.success:
                            errors_encountered.append(f"Tool {result.tool_name}: {result.error}")
                    
                    # Update conversation state
                    conversation_state.last_tool_results = tool_results
                    
                    # Add to conversation history
                    conversation_entry = ConversationEntry(
                        iteration=conversation_state.iteration_count,
                        user_input=user_query if conversation_state.iteration_count == 1 else "Continue",
                        response=action_decision.reasoning,
                        tool_calls_made=action_decision.tool_calls,
                        tool_results=tool_results,
                        timestamp=time.time()
                    )
                    conversation_state.conversation_history.append(conversation_entry)
                    
                    # Check if we should continue
                    if not action_decision.should_continue:
                        return self._create_success_result(
                            activity_id, conversation_state, action_decision,
                            total_tool_calls, list(tools_used), errors_encountered, start_time
                        )
                
                elif action_decision.action_type == ActionType.GOAL_CHECK:
                    # Goal check - just continue to next iteration
                    continue
                
                else:
                    # Default continue behavior
                    continue
            
            # Max iterations reached
            return self._create_max_iterations_result(
                activity_id, conversation_state, total_tool_calls,
                list(tools_used), errors_encountered, start_time
            )
            
        except Exception as e:
            # Unexpected error
            error_msg = f"Unexpected error: {str(e)}"
            errors_encountered.append(error_msg)
            
            return self._create_error_result(
                activity_id, conversation_state, error_msg,
                total_tool_calls, list(tools_used), errors_encountered, start_time
            )
    
    def _execute_tools_sequential(self, tool_calls: List[ToolCall]) -> List[ToolExecutionResult]:
        """
        Execute tools sequentially with error handling.
        
        Args:
            tool_calls: List of tools to execute
            
        Returns:
            List of tool execution results
        """
        results = []
        
        for tool_call in tool_calls:
            try:
                # Execute the tool using the registry
                result = self.tool_registry.execute_tool(tool_call)
                results.append(result)
                
            except Exception as e:
                # Create error result
                error_result = ToolExecutionResult(
                    tool_name=tool_call.tool_name,
                    success=False,
                    result=None,
                    error=str(e),
                    execution_time=0.0,
                    parameters=tool_call.arguments
                )
                results.append(error_result)
        
        return results
    
    def _create_success_result(self, 
                              activity_id: str,
                              conversation_state: ConversationState,
                              final_decision: ActionDecision,
                              total_tool_calls: int,
                              tools_used: List[str],
                              errors_encountered: List[str],
                              start_time: float) -> ActivityResult:
        """Create a successful activity result."""
        return ActivityResult(
            activity_id=activity_id,
            status="completed",
            final_response=final_decision.final_response or "Activity completed successfully.",
            total_iterations=conversation_state.iteration_count,
            total_tool_calls=total_tool_calls,
            execution_time=time.time() - start_time,
            tool_set_name=conversation_state.tool_set_name or "unknown",
            tools_used=tools_used,
            errors_encountered=errors_encountered,
            conversation_state=conversation_state
        )
    
    def _create_error_result(self,
                            activity_id: str,
                            conversation_state: ConversationState,
                            error_message: str,
                            total_tool_calls: int,
                            tools_used: List[str],
                            errors_encountered: List[str],
                            start_time: float) -> ActivityResult:
        """Create an error activity result."""
        return ActivityResult(
            activity_id=activity_id,
            status="error_recovery",
            final_response=f"Activity failed: {error_message}",
            total_iterations=conversation_state.iteration_count,
            total_tool_calls=total_tool_calls,
            execution_time=time.time() - start_time,
            tool_set_name=conversation_state.tool_set_name or "unknown",
            tools_used=tools_used,
            errors_encountered=errors_encountered,
            conversation_state=conversation_state
        )
    
    def _create_timeout_result(self,
                              activity_id: str,
                              conversation_state: ConversationState,
                              total_tool_calls: int,
                              tools_used: List[str],
                              errors_encountered: List[str],
                              start_time: float) -> ActivityResult:
        """Create a timeout activity result."""
        return ActivityResult(
            activity_id=activity_id,
            status="terminated",
            final_response=f"Activity timed out after {self.timeout_seconds} seconds.",
            total_iterations=conversation_state.iteration_count,
            total_tool_calls=total_tool_calls,
            execution_time=time.time() - start_time,
            tool_set_name=conversation_state.tool_set_name or "unknown",
            tools_used=tools_used,
            errors_encountered=errors_encountered,
            conversation_state=conversation_state
        )
    
    def _create_max_iterations_result(self,
                                     activity_id: str,
                                     conversation_state: ConversationState,
                                     total_tool_calls: int,
                                     tools_used: List[str],
                                     errors_encountered: List[str],
                                     start_time: float) -> ActivityResult:
        """Create a max iterations reached result."""
        return ActivityResult(
            activity_id=activity_id,
            status="max_iterations",
            final_response=f"Activity reached maximum iterations ({self.max_iterations}).",
            total_iterations=conversation_state.iteration_count,
            total_tool_calls=total_tool_calls,
            execution_time=time.time() - start_time,
            tool_set_name=conversation_state.tool_set_name or "unknown",
            tools_used=tools_used,
            errors_encountered=errors_encountered,
            conversation_state=conversation_state
        )
    
    def get_available_tools(self) -> List[str]:
        """Get available tools from the tool registry."""
        return self.tool_registry.get_tool_names()
    
    def update_configuration(self, 
                           max_iterations: Optional[int] = None,
                           timeout_seconds: Optional[float] = None):
        """Update activity manager configuration."""
        if max_iterations is not None:
            self.max_iterations = max_iterations
        if timeout_seconds is not None:
            self.timeout_seconds = timeout_seconds