"""
Core reasoning module for the agentic loop implementation.

This module contains the AgentReasoner class which uses DSPy's ChainOfThought
to perform unified reasoning about tool selection and continuation decisions.
"""

from typing import List, Optional
import dspy
from shared.models import ReasoningOutput


class AgentReasonerSignature(dspy.Signature):
    """Unified reasoning signature for agentic loops."""
    
    user_query: str = dspy.InputField(
        desc="The user's original request or question"
    )
    goal: Optional[str] = dspy.InputField(
        desc="Explicit goal if provided by user or previous reasoning"
    )
    conversation_history: str = dspy.InputField(
        desc="Previous tool calls and their results formatted as readable text"
    )
    last_tool_results: Optional[str] = dspy.InputField(
        desc="Results from the most recent tool executions, if any"
    )
    available_tools: str = dspy.InputField(
        desc="JSON array of available tools with their descriptions and parameters"
    )
    iteration_count: int = dspy.InputField(
        desc="Current iteration number in the agent loop"
    )
    max_iterations: int = dspy.InputField(
        desc="Maximum allowed iterations for this activity"
    )
    
    reasoning_output: ReasoningOutput = dspy.OutputField(
        desc="Combined reasoning and decision output with tool selection and continuation logic"
    )


class AgentReasoner(dspy.Module):
    """Core reasoning module for agentic loops using DSPy ChainOfThought."""
    
    def __init__(self, tool_names: List[str], max_iterations: int = 5):
        """
        Initialize the AgentReasoner.
        
        Args:
            tool_names: List of available tool names
            max_iterations: Default maximum iterations
        """
        super().__init__()
        self.tool_names = tool_names
        self.max_iterations = max_iterations
        
        # Main reasoning with Chain of Thought for complex decision making
        self.reasoner = dspy.ChainOfThought(AgentReasonerSignature)
        
        # History summarizer for managing long conversations
        self.history_summarizer = dspy.Predict(
            "long_history -> summary:str, key_points:list[str]"
        )
        
        # Tool relevance analyzer for better tool selection
        self.tool_analyzer = dspy.Predict(
            "user_query, available_tools -> relevant_tools:list[str], reasoning:str"
        )
    
    def forward(self, user_query: str, goal: Optional[str], conversation_history: str, 
                last_tool_results: Optional[str], available_tools: str, 
                iteration_count: int, max_iterations: Optional[int] = None) -> dspy.Prediction:
        """
        Execute unified reasoning about the next action to take.
        
        Args:
            user_query: The user's original request
            goal: Optional explicit goal
            conversation_history: Formatted history of previous interactions
            last_tool_results: Results from most recent tool executions
            available_tools: JSON description of available tools
            iteration_count: Current iteration number
            max_iterations: Maximum allowed iterations (overrides default)
            
        Returns:
            DSPy prediction containing ReasoningOutput
        """
        # Use provided max_iterations or default
        max_iter = max_iterations or self.max_iterations
        
        # Summarize history if it's getting too long
        if len(conversation_history) > 3000:
            conversation_history = self._summarize_history(conversation_history)
        
        # Analyze tool relevance to improve selection
        if iteration_count == 1:  # First iteration
            tool_analysis = self._analyze_tool_relevance(user_query, available_tools)
            # Add tool analysis to reasoning context
            enhanced_query = f"{user_query}\n\nTool Analysis: {tool_analysis}"
        else:
            enhanced_query = user_query
        
        # Main reasoning step
        result = self.reasoner(
            user_query=enhanced_query,
            goal=goal or "No explicit goal provided",
            conversation_history=conversation_history,
            last_tool_results=last_tool_results or "No previous tool results",
            available_tools=available_tools,
            iteration_count=iteration_count,
            max_iterations=max_iter
        )
        
        # Validate and potentially adjust the reasoning output
        result = self._validate_reasoning_output(result, iteration_count, max_iter)
        
        return result
    
    def _summarize_history(self, history: str) -> str:
        """Summarize conversation history if it's getting too long."""
        try:
            summary_result = self.history_summarizer(long_history=history)
            
            # Format the summary for consumption
            summarized = (
                f"[Previous History Summary]: {summary_result.summary}\n"
                f"Key Points: {', '.join(summary_result.key_points)}\n\n"
                f"[Recent History]: {history[-1000:]}"  # Keep last 1000 chars
            )
            return summarized
        except Exception as e:
            # Fallback to simple truncation if summarization fails
            return f"[History Truncated]: {history[-2000:]}"
    
    def _analyze_tool_relevance(self, user_query: str, available_tools: str) -> str:
        """Analyze which tools might be most relevant for the user query."""
        try:
            analysis = self.tool_analyzer(
                user_query=user_query,
                available_tools=available_tools
            )
            
            return f"Most relevant tools: {', '.join(analysis.relevant_tools)}. {analysis.reasoning}"
        except Exception as e:
            return f"Tool analysis failed: {str(e)}"
    
    def _validate_reasoning_output(self, result: dspy.Prediction, 
                                 iteration_count: int, max_iterations: int) -> dspy.Prediction:
        """Validate and potentially adjust the reasoning output."""
        reasoning_output = result.reasoning_output
        
        # Ensure we don't exceed max iterations
        if iteration_count >= max_iterations:
            reasoning_output.should_continue = False
            reasoning_output.continuation_reasoning = f"Maximum iterations ({max_iterations}) reached"
            if not reasoning_output.final_response:
                reasoning_output.final_response = "I've reached the maximum number of iterations. Based on the work completed so far, here's what I found."
        
        # Validate tool calls if present
        if reasoning_output.should_use_tools and reasoning_output.tool_calls:
            # Ensure tool names are valid
            valid_tool_calls = []
            for tool_call in reasoning_output.tool_calls:
                if tool_call.tool_name in self.tool_names:
                    valid_tool_calls.append(tool_call)
                else:
                    # Log invalid tool name but continue
                    print(f"Warning: Invalid tool name '{tool_call.tool_name}' ignored")
            
            reasoning_output.tool_calls = valid_tool_calls
            
            # If no valid tools remain, adjust decision
            if not valid_tool_calls:
                reasoning_output.should_use_tools = False
                reasoning_output.continuation_reasoning = "No valid tools available for selected actions"
        
        # Ensure consistency between should_use_tools and tool_calls
        if reasoning_output.should_use_tools and not reasoning_output.tool_calls:
            reasoning_output.should_use_tools = False
            reasoning_output.continuation_reasoning = "No specific tools identified for execution"
        
        # Ensure we have a final response if not continuing
        if not reasoning_output.should_continue and not reasoning_output.final_response:
            reasoning_output.final_response = "I've completed the analysis based on the available information."
        
        return result
    
    def get_available_tools(self) -> List[str]:
        """Get the list of available tool names."""
        return self.tool_names.copy()
    
    def update_tool_names(self, tool_names: List[str]):
        """Update the available tool names."""
        self.tool_names = tool_names