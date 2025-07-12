"""
Goal Tracker for advanced agentic loop.

This module tracks progress toward completing goals and helps determine
when a multi-step task is complete.
"""

from typing import List, Optional, Dict
import dspy
from pydantic import BaseModel, Field


class GoalProgress(BaseModel):
    """Tracks progress toward completing a goal."""
    original_goal: str = Field(desc="The original user goal or request")
    sub_goals: List[str] = Field(
        default_factory=list,
        desc="List of identified sub-goals that need to be completed"
    )
    completed_steps: List[str] = Field(
        default_factory=list,
        desc="List of steps that have been successfully completed"
    )
    pending_steps: List[str] = Field(
        default_factory=list,
        desc="List of steps that still need to be completed"
    )
    completion_percentage: float = Field(
        default=0.0,
        desc="Estimated percentage of goal completion (0.0 to 100.0)"
    )
    is_complete: bool = Field(
        default=False,
        desc="Whether the goal has been fully achieved"
    )
    blockers: List[str] = Field(
        default_factory=list,
        desc="Any identified blockers preventing goal completion"
    )


class GoalTrackerSignature(dspy.Signature):
    """Track and evaluate goal completion progress."""
    
    original_goal: str = dspy.InputField(
        desc="The original user goal or request"
    )
    tool_results: List[Dict[str, str]] = dspy.InputField(
        desc="List of tool execution results with tool names and outcomes"
    )
    conversation_history: str = dspy.InputField(
        desc="Formatted conversation history showing all interactions"
    )
    iteration_count: int = dspy.InputField(
        desc="Current iteration number in the agent loop"
    )
    
    goal_progress: GoalProgress = dspy.OutputField(
        desc="Current progress toward goal completion with detailed tracking"
    )
    should_continue: bool = dspy.OutputField(
        desc="Whether the agent should continue working toward the goal"
    )
    next_priority: str = dspy.OutputField(
        desc="The most important next step to take if continuing"
    )


class GoalDecompositionSignature(dspy.Signature):
    """Decompose a high-level goal into actionable sub-goals."""
    
    goal: str = dspy.InputField(
        desc="The high-level goal to decompose"
    )
    available_tools: List[str] = dspy.InputField(
        desc="List of available tools that can be used"
    )
    
    sub_goals: List[str] = dspy.OutputField(
        desc="List of concrete sub-goals in logical order"
    )
    dependencies: Dict[str, List[str]] = dspy.OutputField(
        desc="Dependencies between sub-goals (goal -> list of prerequisite goals)"
    )


class GoalTracker(dspy.Module):
    """
    Tracks and evaluates goal completion progress in the agentic loop.
    
    This module helps determine when complex multi-step tasks are complete
    and what steps remain.
    """
    
    def __init__(self):
        super().__init__()
        # Main goal tracking with Chain of Thought
        self.goal_analyzer = dspy.ChainOfThought(GoalTrackerSignature)
        
        # Goal decomposition for complex tasks
        self.goal_decomposer = dspy.ChainOfThought(GoalDecompositionSignature)
        
        # Progress estimator
        self.progress_estimator = dspy.Predict(
            "completed_steps: list[str], total_steps: list[str] -> "
            "percentage: float, confidence: float"
        )
    
    def forward(
        self,
        original_goal: str,
        tool_results: List[Dict[str, str]],
        conversation_history: str,
        iteration_count: int,
        available_tools: Optional[List[str]] = None
    ) -> dspy.Prediction:
        """
        Track goal progress and determine if continuation is needed.
        
        Args:
            original_goal: The user's original request
            tool_results: List of tool execution results
            conversation_history: Formatted conversation history
            iteration_count: Current iteration number
            available_tools: Optional list of available tools for decomposition
            
        Returns:
            DSPy prediction containing goal progress and continuation decision
        """
        # Decompose goal if this is the first iteration and tools are available
        if iteration_count == 1 and available_tools:
            decomposition = self.goal_decomposer(
                goal=original_goal,
                available_tools=available_tools
            )
            
            # Add decomposition info to conversation history
            enhanced_history = (
                f"Goal Decomposition:\n"
                f"Sub-goals: {', '.join(decomposition.sub_goals)}\n\n"
                f"{conversation_history}"
            )
        else:
            enhanced_history = conversation_history
        
        # Main goal tracking analysis
        result = self.goal_analyzer(
            original_goal=original_goal,
            tool_results=tool_results,
            conversation_history=enhanced_history,
            iteration_count=iteration_count
        )
        
        # Validate and enhance the result
        result = self._validate_progress(result)
        
        # Estimate completion percentage if not provided
        if result.goal_progress.completed_steps and result.goal_progress.sub_goals:
            progress_est = self.progress_estimator(
                completed_steps=result.goal_progress.completed_steps,
                total_steps=result.goal_progress.sub_goals
            )
            
            # Use estimated percentage if the analyzer didn't provide one
            if result.goal_progress.completion_percentage == 0.0:
                result.goal_progress.completion_percentage = progress_est.percentage
        
        return result
    
    def _validate_progress(self, result: dspy.Prediction) -> dspy.Prediction:
        """Validate and adjust the goal progress if needed."""
        progress = result.goal_progress
        
        # Ensure percentage is in valid range
        progress.completion_percentage = max(0.0, min(100.0, progress.completion_percentage))
        
        # If 100% complete, ensure is_complete is True
        if progress.completion_percentage >= 100.0:
            progress.is_complete = True
        
        # If complete, we shouldn't continue
        if progress.is_complete:
            result.should_continue = False
            result.next_priority = "Goal completed"
        
        # If there are blockers and no pending steps, don't continue
        if progress.blockers and not progress.pending_steps:
            result.should_continue = False
            result.next_priority = f"Blocked by: {', '.join(progress.blockers)}"
        
        # Ensure pending steps are actually pending (not in completed)
        progress.pending_steps = [
            step for step in progress.pending_steps 
            if step not in progress.completed_steps
        ]
        
        return result
    
    def update_progress(
        self,
        current_progress: GoalProgress,
        new_completed_step: str,
        new_tool_results: Optional[Dict[str, str]] = None
    ) -> GoalProgress:
        """
        Update goal progress with a newly completed step.
        
        Args:
            current_progress: Current goal progress state
            new_completed_step: Step that was just completed
            new_tool_results: Optional results from tool execution
            
        Returns:
            Updated goal progress
        """
        # Add to completed steps if not already there
        if new_completed_step not in current_progress.completed_steps:
            current_progress.completed_steps.append(new_completed_step)
        
        # Remove from pending if present
        if new_completed_step in current_progress.pending_steps:
            current_progress.pending_steps.remove(new_completed_step)
        
        # Recalculate completion percentage
        total_steps = len(current_progress.sub_goals)
        if total_steps > 0:
            completed = len(current_progress.completed_steps)
            current_progress.completion_percentage = (completed / total_steps) * 100.0
        
        # Check if complete
        if not current_progress.pending_steps and current_progress.sub_goals:
            current_progress.is_complete = True
            current_progress.completion_percentage = 100.0
        
        return current_progress
    
    def suggest_next_steps(
        self,
        goal_progress: GoalProgress,
        available_tools: List[str]
    ) -> List[str]:
        """
        Suggest the next steps based on current progress.
        
        Args:
            goal_progress: Current goal progress
            available_tools: List of available tools
            
        Returns:
            List of suggested next steps in priority order
        """
        suggestions = []
        
        # First, try to complete any pending steps
        for step in goal_progress.pending_steps:
            if not any(blocker in step for blocker in goal_progress.blockers):
                suggestions.append(step)
        
        # If no pending steps, check if we need to identify new sub-goals
        if not suggestions and not goal_progress.is_complete:
            suggestions.append("Identify additional steps needed to complete the goal")
        
        return suggestions[:3]  # Return top 3 suggestions