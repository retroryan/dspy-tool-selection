"""
Advanced Agent Reasoner with enhanced capabilities.

This module extends the basic AgentReasoner with tool result analysis,
goal tracking, and dynamic adaptation capabilities.
"""

from typing import List, Optional, Dict, Any
import dspy
from shared.models import ReasoningOutput, ToolCall
from agentic_loop.agent_reasoner import AgentReasoner, AgentReasonerSignature
from .tool_result_analyzer import ToolResultAnalyzer, ToolResultAnalysis
from .goal_tracker import GoalTracker, GoalProgress


class AdvancedReasoningOutput(ReasoningOutput):
    """Extended reasoning output with advanced features."""
    goal_progress: Optional[GoalProgress] = None
    tool_analysis: Optional[ToolResultAnalysis] = None
    adaptation_strategy: Optional[str] = None
    confidence_score: float = 0.8


class AdvancedAgentReasonerSignature(AgentReasonerSignature):
    """Enhanced reasoning signature with additional context."""
    
    # Additional input fields
    goal_progress: Optional[str] = dspy.InputField(
        desc="Current progress toward goal completion in JSON format",
        default=None
    )
    successful_tools: Optional[str] = dspy.InputField(
        desc="List of successfully executed tools so far",
        default=None
    )
    failed_attempts: Optional[str] = dspy.InputField(
        desc="List of failed tool attempts with error messages",
        default=None
    )
    
    # Override output to use advanced version
    reasoning_output: AdvancedReasoningOutput = dspy.OutputField(
        desc="Advanced reasoning output with goal tracking and tool analysis"
    )


class AdvancedAgentReasoner(AgentReasoner):
    """
    Advanced reasoning module with enhanced decision-making capabilities.
    
    Extends the basic AgentReasoner with:
    - Tool result analysis for better follow-up decisions
    - Goal tracking for multi-step task completion
    - Dynamic strategy adaptation based on results
    - Enhanced error recovery mechanisms
    """
    
    def __init__(self, tool_names: List[str], max_iterations: int = 10):
        """
        Initialize the AdvancedAgentReasoner.
        
        Args:
            tool_names: List of available tool names
            max_iterations: Maximum iterations (default higher for complex tasks)
        """
        # Initialize parent with higher default iterations
        super().__init__(tool_names, max_iterations)
        
        # Initialize advanced components
        self.tool_result_analyzer = ToolResultAnalyzer()
        self.goal_tracker = GoalTracker()
        
        # Override main reasoner with advanced signature
        self.reasoner = dspy.ChainOfThought(AdvancedAgentReasonerSignature)
        
        # Add strategy selector for dynamic adaptation
        self.strategy_selector = dspy.Predict(
            "current_progress: str, failed_attempts: int, remaining_iterations: int -> "
            "strategy: str, risk_tolerance: float"
        )
        
        # Add confidence estimator
        self.confidence_estimator = dspy.Predict(
            "reasoning: str, tool_analysis: str, goal_progress: str -> "
            "confidence_score: float, reliability_factors: list[str]"
        )
    
    def forward(
        self,
        user_query: str,
        goal: Optional[str],
        conversation_history: str,
        last_tool_results: Optional[str],
        available_tools: str,
        iteration_count: int,
        max_iterations: Optional[int] = None,
        **kwargs
    ) -> dspy.Prediction:
        """
        Execute advanced reasoning about the next action to take.
        
        Args:
            user_query: The user's original request
            goal: Optional explicit goal
            conversation_history: Formatted history of previous interactions
            last_tool_results: Results from most recent tool executions
            available_tools: JSON description of available tools
            iteration_count: Current iteration number
            max_iterations: Maximum allowed iterations
            **kwargs: Additional context (goal_progress, successful_tools, etc.)
            
        Returns:
            DSPy prediction containing AdvancedReasoningOutput
        """
        # Use provided max_iterations or default
        max_iter = max_iterations or self.max_iterations
        
        # Extract advanced context from kwargs
        goal_progress_str = kwargs.get('goal_progress', None)
        successful_tools = kwargs.get('successful_tools', None)
        failed_attempts = kwargs.get('failed_attempts', None)
        
        # Analyze last tool results if available
        tool_analysis = None
        if last_tool_results and iteration_count > 1:
            # Parse tool results to analyze
            tool_analysis = self._analyze_tool_results(
                last_tool_results,
                goal or user_query,
                self.tool_names
            )
        
        # Track goal progress
        goal_progress = None
        if iteration_count >= 1:
            goal_progress = self._track_goal_progress(
                original_goal=goal or user_query,
                conversation_history=conversation_history,
                iteration_count=iteration_count,
                tool_results_str=last_tool_results
            )
        
        # Select adaptation strategy
        strategy = self._select_strategy(
            iteration_count=iteration_count,
            max_iterations=max_iter,
            goal_progress=goal_progress,
            failed_attempts=failed_attempts
        )
        
        # Prepare enhanced context
        enhanced_query = self._prepare_enhanced_context(
            user_query=user_query,
            tool_analysis=tool_analysis,
            goal_progress=goal_progress,
            strategy=strategy
        )
        
        # Main reasoning with enhanced context
        result = self.reasoner(
            user_query=enhanced_query,
            goal=goal or "No explicit goal provided",
            conversation_history=conversation_history,
            last_tool_results=last_tool_results or "No previous tool results",
            available_tools=available_tools,
            iteration_count=iteration_count,
            max_iterations=max_iter,
            goal_progress=str(goal_progress.model_dump()) if goal_progress else None,
            successful_tools=successful_tools,
            failed_attempts=failed_attempts
        )
        
        # Enhance reasoning output with advanced features
        result = self._enhance_reasoning_output(
            result, tool_analysis, goal_progress, strategy
        )
        
        # Estimate confidence in the decision
        confidence = self._estimate_confidence(result)
        result.reasoning_output.confidence_score = confidence
        
        return result
    
    def _analyze_tool_results(
        self,
        tool_results_str: str,
        original_goal: str,
        available_tools: List[str]
    ) -> Optional[ToolResultAnalysis]:
        """Analyze the most recent tool execution results."""
        try:
            # Parse tool results (assuming formatted string)
            # In real implementation, this would parse structured data
            tool_name = "unknown"
            tool_result = tool_results_str
            
            # Extract tool name if formatted properly
            if "Tool:" in tool_results_str:
                parts = tool_results_str.split("Tool:", 1)
                if len(parts) > 1:
                    tool_name = parts[1].split("\n")[0].strip()
            
            analysis = self.tool_result_analyzer(
                tool_name=tool_name,
                tool_result=tool_result,
                original_goal=original_goal,
                available_tools=available_tools
            )
            
            return analysis.analysis
        except Exception as e:
            print(f"Tool analysis failed: {e}")
            return None
    
    def _track_goal_progress(
        self,
        original_goal: str,
        conversation_history: str,
        iteration_count: int,
        tool_results_str: Optional[str]
    ) -> Optional[GoalProgress]:
        """Track progress toward goal completion."""
        try:
            # Parse tool results into structured format
            tool_results = []
            if tool_results_str:
                # Simple parsing - in real implementation would be more robust
                tool_results.append({
                    "tool_name": "recent_execution",
                    "result": tool_results_str
                })
            
            tracking = self.goal_tracker(
                original_goal=original_goal,
                tool_results=tool_results,
                conversation_history=conversation_history,
                iteration_count=iteration_count,
                available_tools=self.tool_names
            )
            
            return tracking.goal_progress
        except Exception as e:
            print(f"Goal tracking failed: {e}")
            return None
    
    def _select_strategy(
        self,
        iteration_count: int,
        max_iterations: int,
        goal_progress: Optional[GoalProgress],
        failed_attempts: Optional[str]
    ) -> str:
        """Select adaptation strategy based on current state."""
        try:
            # Count failed attempts
            num_failures = 0
            if failed_attempts:
                num_failures = failed_attempts.count("failed")
            
            # Determine current progress level
            progress_str = "unknown"
            if goal_progress:
                if goal_progress.completion_percentage > 75:
                    progress_str = "nearly_complete"
                elif goal_progress.completion_percentage > 50:
                    progress_str = "good_progress"
                elif goal_progress.completion_percentage > 25:
                    progress_str = "some_progress"
                else:
                    progress_str = "minimal_progress"
            
            remaining = max_iterations - iteration_count
            
            strategy_result = self.strategy_selector(
                current_progress=progress_str,
                failed_attempts=num_failures,
                remaining_iterations=remaining
            )
            
            return strategy_result.strategy
        except Exception as e:
            # Default strategy on error
            if iteration_count > max_iterations * 0.7:
                return "conservative"
            else:
                return "balanced"
    
    def _prepare_enhanced_context(
        self,
        user_query: str,
        tool_analysis: Optional[ToolResultAnalysis],
        goal_progress: Optional[GoalProgress],
        strategy: str
    ) -> str:
        """Prepare enhanced context for reasoning."""
        enhanced = user_query
        
        if tool_analysis:
            enhanced += f"\n\nTool Analysis: {tool_analysis.reasoning}"
            if tool_analysis.suggested_next_tools:
                enhanced += f"\nSuggested tools: {', '.join(tool_analysis.suggested_next_tools)}"
        
        if goal_progress:
            enhanced += f"\n\nGoal Progress: {goal_progress.completion_percentage:.0f}% complete"
            if goal_progress.pending_steps:
                enhanced += f"\nPending: {', '.join(goal_progress.pending_steps[:2])}"
        
        enhanced += f"\n\nStrategy: {strategy}"
        
        return enhanced
    
    def _enhance_reasoning_output(
        self,
        result: dspy.Prediction,
        tool_analysis: Optional[ToolResultAnalysis],
        goal_progress: Optional[GoalProgress],
        strategy: str
    ) -> dspy.Prediction:
        """Enhance the reasoning output with advanced features."""
        # Add advanced features to reasoning output
        if hasattr(result.reasoning_output, 'goal_progress'):
            result.reasoning_output.goal_progress = goal_progress
        
        if hasattr(result.reasoning_output, 'tool_analysis'):
            result.reasoning_output.tool_analysis = tool_analysis
        
        if hasattr(result.reasoning_output, 'adaptation_strategy'):
            result.reasoning_output.adaptation_strategy = strategy
        
        # Adjust decisions based on goal progress
        if goal_progress and goal_progress.is_complete:
            result.reasoning_output.should_continue = False
            if not result.reasoning_output.final_response:
                result.reasoning_output.final_response = (
                    f"I've successfully completed the task. "
                    f"Goal achieved: {goal_progress.original_goal}"
                )
        
        # Use tool analysis suggestions if available
        if (tool_analysis and tool_analysis.suggested_next_tools and 
            result.reasoning_output.should_use_tools):
            # Enhance tool selection with suggestions
            suggested_calls = [
                ToolCall(tool_name=tool_name, arguments={})
                for tool_name in tool_analysis.suggested_next_tools
                if tool_name in self.tool_names
            ]
            
            # Merge with existing tool calls
            if result.reasoning_output.tool_calls:
                existing_names = {tc.tool_name for tc in result.reasoning_output.tool_calls}
                for sc in suggested_calls:
                    if sc.tool_name not in existing_names:
                        result.reasoning_output.tool_calls.append(sc)
            else:
                result.reasoning_output.tool_calls = suggested_calls
        
        return result
    
    def _estimate_confidence(self, result: dspy.Prediction) -> float:
        """Estimate confidence in the reasoning decision."""
        try:
            reasoning_text = ""
            if hasattr(result, 'reasoning'):
                reasoning_text = result.reasoning
            
            tool_analysis_text = ""
            if hasattr(result.reasoning_output, 'tool_analysis') and result.reasoning_output.tool_analysis:
                tool_analysis_text = result.reasoning_output.tool_analysis.reasoning
            
            goal_progress_text = ""
            if hasattr(result.reasoning_output, 'goal_progress') and result.reasoning_output.goal_progress:
                goal_progress_text = f"Progress: {result.reasoning_output.goal_progress.completion_percentage}%"
            
            confidence_result = self.confidence_estimator(
                reasoning=reasoning_text,
                tool_analysis=tool_analysis_text,
                goal_progress=goal_progress_text
            )
            
            return max(0.0, min(1.0, confidence_result.confidence_score))
        except Exception as e:
            # Default confidence on error
            return 0.7
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get the advanced capabilities of this reasoner."""
        base_capabilities = {
            "tool_names": self.tool_names,
            "max_iterations": self.max_iterations
        }
        
        advanced_capabilities = {
            "features": [
                "tool_result_analysis",
                "goal_tracking",
                "dynamic_strategy_adaptation",
                "confidence_estimation",
                "enhanced_error_recovery"
            ],
            "components": {
                "tool_analyzer": "ToolResultAnalyzer",
                "goal_tracker": "GoalTracker",
                "strategy_selector": "Dynamic strategy selection",
                "confidence_estimator": "Decision confidence estimation"
            }
        }
        
        return {**base_capabilities, **advanced_capabilities}