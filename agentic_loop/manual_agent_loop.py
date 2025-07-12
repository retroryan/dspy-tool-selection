"""
Manual Agent Loop implementation for DSPy-based tool selection.

This module provides a stateless agent loop that uses DSPy for LLM reasoning
while maintaining external control over tool execution and iteration.
"""

from typing import List, Optional, Dict, Any
import json
import dspy
from shared.models import (
    ActionDecision,
    ActionType,
    ConversationState,
    ToolExecutionResult,
    ReasoningOutput
)
from agentic_loop.agent_reasoner import AgentReasoner


class ManualAgentLoop(dspy.Module):
    """
    Manual agent loop with external control via ActivityManager.
    
    This class provides stateless operation where each call receives full context
    and returns decisions for external execution control.
    """
    
    def __init__(self, tool_names: List[str], max_iterations: int = 5):
        """
        Initialize the ManualAgentLoop.
        
        Args:
            tool_names: List of available tool names
            max_iterations: Default maximum iterations per activity
        """
        super().__init__()
        self.tool_names = tool_names
        self.max_iterations = max_iterations
        
        # Core reasoning module
        self.agent_reasoner = AgentReasoner(tool_names, max_iterations)
    
    def forward(self, conversation_state: ConversationState) -> dspy.Prediction:
        """
        DSPy forward method for compatibility.
        
        Args:
            conversation_state: Complete conversation state
            
        Returns:
            DSPy prediction containing ActionDecision
        """
        return self.get_next_action(conversation_state)
    
    def get_next_action(self, conversation_state: ConversationState) -> ActionDecision:
        """
        Main entry point for external ActivityManager control.
        
        This method analyzes the current conversation state and returns
        a decision about what action to take next.
        
        Args:
            conversation_state: Complete conversation state with history
            
        Returns:
            ActionDecision with next action and reasoning
        """
        try:
            # Format conversation history for LLM consumption
            formatted_history = self._format_conversation_history(conversation_state)
            
            # Format tool results from last iteration
            formatted_tool_results = self._format_tool_results(
                conversation_state.last_tool_results
            )
            
            # Format available tools for LLM
            available_tools = self._format_available_tools()
            
            # Perform core reasoning
            reasoning_result = self._perform_core_reasoning(
                user_query=conversation_state.user_query,
                goal=conversation_state.goal,
                conversation_history=formatted_history,
                last_tool_results=formatted_tool_results,
                available_tools=available_tools,
                iteration_count=conversation_state.iteration_count,
                max_iterations=conversation_state.max_iterations or self.max_iterations
            )
            
            # Convert reasoning output to action decision
            return self._create_action_decision(reasoning_result, conversation_state)
            
        except Exception as e:
            # Handle errors gracefully
            return self._create_error_decision(str(e), conversation_state)
    
    def _perform_core_reasoning(self, user_query: str, goal: Optional[str],
                              conversation_history: str, last_tool_results: Optional[str],
                              available_tools: str, iteration_count: int,
                              max_iterations: int) -> ReasoningOutput:
        """
        Perform core reasoning using AgentReasoner.
        
        Args:
            user_query: Original user request
            goal: Optional explicit goal
            conversation_history: Formatted conversation history
            last_tool_results: Results from previous tool executions
            available_tools: JSON formatted available tools
            iteration_count: Current iteration number
            max_iterations: Maximum allowed iterations
            
        Returns:
            ReasoningOutput with decision and reasoning
        """
        # Use the agent reasoner for unified reasoning
        result = self.agent_reasoner(
            user_query=user_query,
            goal=goal,
            conversation_history=conversation_history,
            last_tool_results=last_tool_results,
            available_tools=available_tools,
            iteration_count=iteration_count,
            max_iterations=max_iterations
        )
        
        return result.reasoning_output
    
    def _format_conversation_history(self, conversation_state: ConversationState) -> str:
        """
        Format conversation history for LLM consumption.
        
        Args:
            conversation_state: Current conversation state
            
        Returns:
            Formatted conversation history as string
        """
        if not conversation_state.conversation_history:
            return "No previous conversation history."
        
        # Format each entry in the history
        formatted_entries = []
        for entry in conversation_state.conversation_history:
            formatted_entries.append(
                f"Iteration {entry.iteration}: {entry.user_input} -> {entry.response}"
            )
        
        return "\n".join(formatted_entries)
    
    def _format_tool_results(self, tool_results: Optional[List[ToolExecutionResult]]) -> Optional[str]:
        """
        Format tool execution results for LLM consumption.
        
        Args:
            tool_results: List of tool execution results
            
        Returns:
            Formatted tool results as string or None
        """
        if not tool_results:
            return None
        
        formatted_results = []
        for result in tool_results:
            if result.success:
                formatted_results.append(
                    f"Tool '{result.tool_name}' succeeded: {result.result}"
                )
            else:
                formatted_results.append(
                    f"Tool '{result.tool_name}' failed: {result.error}"
                )
        
        return "\n".join(formatted_results)
    
    def _format_available_tools(self) -> str:
        """
        Format available tools for LLM consumption.
        
        Returns:
            JSON formatted string of available tools
        """
        # Simple tool format - this could be enhanced with tool descriptions
        tools = [{"name": name, "description": f"Tool for {name} operations"} 
                for name in self.tool_names]
        
        return json.dumps(tools, indent=2)
    
    def _create_action_decision(self, reasoning_output: ReasoningOutput,
                              conversation_state: ConversationState) -> ActionDecision:
        """
        Create ActionDecision from reasoning output.
        
        Args:
            reasoning_output: Output from core reasoning
            conversation_state: Current conversation state
            
        Returns:
            ActionDecision for external execution
        """
        # Determine action type
        if reasoning_output.should_use_tools and reasoning_output.tool_calls:
            action_type = ActionType.TOOL_EXECUTION
        elif not reasoning_output.should_continue:
            action_type = ActionType.FINAL_RESPONSE
        else:
            action_type = ActionType.CONTINUE
        
        return ActionDecision(
            action_type=action_type,
            tool_calls=reasoning_output.tool_calls or [],
            reasoning=reasoning_output.overall_reasoning,
            should_continue=reasoning_output.should_continue,
            continuation_reasoning=reasoning_output.continuation_reasoning,
            final_response=reasoning_output.final_response,
            confidence_score=reasoning_output.confidence,
            iteration_count=conversation_state.iteration_count,
            max_iterations=conversation_state.max_iterations or self.max_iterations
        )
    
    def _create_error_decision(self, error_message: str,
                             conversation_state: ConversationState) -> ActionDecision:
        """
        Create ActionDecision for error scenarios.
        
        Args:
            error_message: Error that occurred
            conversation_state: Current conversation state
            
        Returns:
            ActionDecision indicating error state
        """
        return ActionDecision(
            action_type=ActionType.ERROR_RECOVERY,
            tool_calls=[],
            reasoning=f"Error occurred during reasoning: {error_message}",
            should_continue=False,
            continuation_reasoning="Stopping due to error",
            final_response=f"I encountered an error: {error_message}",
            confidence_score=0.0,
            iteration_count=conversation_state.iteration_count,
            max_iterations=conversation_state.max_iterations or self.max_iterations
        )
    
    def get_available_tools(self) -> List[str]:
        """Get the list of available tool names."""
        return self.tool_names.copy()
    
    def update_tool_names(self, tool_names: List[str]):
        """Update the available tool names."""
        self.tool_names = tool_names
        self.agent_reasoner.update_tool_names(tool_names)