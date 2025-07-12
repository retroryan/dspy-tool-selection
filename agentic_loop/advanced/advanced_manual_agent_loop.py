"""
Advanced Manual Agent Loop with enhanced reasoning capabilities.

This module extends the basic ManualAgentLoop to use the AdvancedAgentReasoner
and provides additional features for multi-step task handling.
"""

from typing import List, Optional, Dict, Any
from shared.models import ConversationState, ActionDecision
from agentic_loop.manual_agent_loop import ManualAgentLoop
from .advanced_agent_reasoner import AdvancedAgentReasoner


class AdvancedManualAgentLoop(ManualAgentLoop):
    """
    Advanced version of ManualAgentLoop with enhanced reasoning.
    
    This class uses the AdvancedAgentReasoner to provide:
    - Tool result analysis
    - Goal tracking
    - Dynamic strategy adaptation
    - Enhanced error recovery
    """
    
    def __init__(self, tool_names: List[str], max_iterations: int = 10):
        """
        Initialize the AdvancedManualAgentLoop.
        
        Args:
            tool_names: List of available tool names
            max_iterations: Maximum iterations (default higher for complex tasks)
        """
        # Initialize parent
        super().__init__(tool_names, max_iterations)
        
        # Replace the basic reasoner with advanced version
        self.agent_reasoner = AdvancedAgentReasoner(
            tool_names=tool_names,
            max_iterations=max_iterations
        )
        
        # Track additional context for advanced features
        self.successful_tools: List[str] = []
        self.failed_attempts: List[Dict[str, str]] = []
    
    def get_next_action(self, state: ConversationState) -> ActionDecision:
        """
        Get the next action with enhanced reasoning capabilities.
        
        Args:
            state: Current conversation state
            
        Returns:
            ActionDecision with next action to take
        """
        # Update tracking based on last results
        if state.last_tool_results:
            for result in state.last_tool_results:
                if result.success:
                    if result.tool_name not in self.successful_tools:
                        self.successful_tools.append(result.tool_name)
                else:
                    self.failed_attempts.append({
                        "tool": result.tool_name,
                        "error": result.error or "Unknown error"
                    })
        
        # Prepare enhanced context
        enhanced_kwargs = {
            "successful_tools": ", ".join(self.successful_tools) if self.successful_tools else None,
            "failed_attempts": str(self.failed_attempts) if self.failed_attempts else None
        }
        
        # Call parent method with enhanced context
        # The parent will use our advanced reasoner
        return super().get_next_action(state, **enhanced_kwargs)
    
    def _convert_to_action_decision(self, reasoning_output: Any) -> ActionDecision:
        """
        Convert reasoning output to ActionDecision with advanced features.
        
        Args:
            reasoning_output: Output from AdvancedAgentReasoner
            
        Returns:
            ActionDecision with enhanced information
        """
        # Use parent conversion
        decision = super()._convert_to_action_decision(reasoning_output)
        
        # Add advanced information if available
        if hasattr(reasoning_output, 'goal_progress') and reasoning_output.goal_progress:
            # Enhance final response with progress info
            if decision.final_response and reasoning_output.goal_progress.is_complete:
                decision.final_response += (
                    f"\n\nGoal completed: {reasoning_output.goal_progress.completion_percentage:.0f}% "
                    f"({len(reasoning_output.goal_progress.completed_steps)} steps completed)"
                )
        
        if hasattr(reasoning_output, 'confidence_score'):
            # Add confidence to reasoning
            decision.reasoning += f"\n[Confidence: {reasoning_output.confidence_score:.2f}]"
        
        return decision
    
    def reset_tracking(self):
        """Reset the tracking state for a new conversation."""
        self.successful_tools = []
        self.failed_attempts = []
    
    def get_advanced_metrics(self) -> Dict[str, Any]:
        """Get metrics about the advanced features."""
        return {
            "successful_tools": self.successful_tools,
            "failed_attempts": len(self.failed_attempts),
            "unique_tools_used": len(set(self.successful_tools)),
            "reasoner_capabilities": self.agent_reasoner.get_capabilities()
        }