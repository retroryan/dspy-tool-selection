"""
Tool Result Analyzer for advanced agentic loop.

This module analyzes tool execution results to determine next steps and
guide the agent's decision-making process.
"""

from typing import List, Optional
import dspy
from pydantic import BaseModel, Field


class ToolResultAnalysis(BaseModel):
    """Analysis of tool execution results."""
    is_successful: bool = Field(desc="Whether the tool execution was successful")
    needs_followup: bool = Field(desc="Whether follow-up actions are needed")
    suggested_next_tools: List[str] = Field(
        default_factory=list,
        desc="List of tool names that should be executed next"
    )
    reasoning: str = Field(desc="Detailed reasoning about the tool results")
    confidence_score: float = Field(
        default=0.0,
        desc="Confidence in the analysis (0.0 to 1.0)"
    )


class ToolResultAnalyzerSignature(dspy.Signature):
    """Analyze tool execution results to guide next actions."""
    
    tool_name: str = dspy.InputField(
        desc="Name of the tool that was executed"
    )
    tool_result: str = dspy.InputField(
        desc="The result returned by the tool (success or error)"
    )
    original_goal: str = dspy.InputField(
        desc="The original user goal or request"
    )
    available_tools: List[str] = dspy.InputField(
        desc="List of available tool names that can be used"
    )
    previous_tools_used: List[str] = dspy.InputField(
        desc="List of tools already used in this conversation",
        default_factory=list
    )
    
    analysis: ToolResultAnalysis = dspy.OutputField(
        desc="Structured analysis of the tool result with recommendations"
    )


class ToolResultAnalyzer(dspy.Module):
    """
    Analyzes tool execution results to guide next actions in the agentic loop.
    
    This module uses Chain of Thought reasoning to understand tool results
    and recommend appropriate follow-up actions.
    """
    
    def __init__(self):
        super().__init__()
        # Use ChainOfThought for better reasoning about tool results
        self.analyzer = dspy.ChainOfThought(ToolResultAnalyzerSignature)
        
        # Additional predictor for error recovery strategies
        self.error_analyzer = dspy.Predict(
            "error_message, tool_name, available_tools -> recovery_strategy: str, alternative_tools: list[str]"
        )
    
    def forward(
        self,
        tool_name: str,
        tool_result: str,
        original_goal: str,
        available_tools: List[str],
        previous_tools_used: Optional[List[str]] = None
    ) -> dspy.Prediction:
        """
        Analyze tool results and provide recommendations.
        
        Args:
            tool_name: Name of the executed tool
            tool_result: Result or error from tool execution
            original_goal: The user's original request
            available_tools: List of available tool names
            previous_tools_used: Tools already used in this conversation
            
        Returns:
            DSPy prediction containing ToolResultAnalysis
        """
        # Default to empty list if not provided
        if previous_tools_used is None:
            previous_tools_used = []
        
        # Check if this appears to be an error
        is_error = any(error_indicator in tool_result.lower() 
                      for error_indicator in ["error", "failed", "exception", "invalid"])
        
        if is_error:
            # Use error analyzer for recovery strategies
            error_recovery = self.error_analyzer(
                error_message=tool_result,
                tool_name=tool_name,
                available_tools=available_tools
            )
            
            # Enhance the tool result with recovery information
            enhanced_result = (
                f"{tool_result}\n\n"
                f"Recovery Strategy: {error_recovery.recovery_strategy}"
            )
        else:
            enhanced_result = tool_result
        
        # Main analysis
        result = self.analyzer(
            tool_name=tool_name,
            tool_result=enhanced_result,
            original_goal=original_goal,
            available_tools=available_tools,
            previous_tools_used=previous_tools_used
        )
        
        # Validate the analysis
        result = self._validate_analysis(result, available_tools)
        
        return result
    
    def _validate_analysis(self, result: dspy.Prediction, available_tools: List[str]) -> dspy.Prediction:
        """Validate and adjust the analysis if needed."""
        analysis = result.analysis
        
        # Ensure suggested tools are actually available
        valid_suggestions = [
            tool for tool in analysis.suggested_next_tools 
            if tool in available_tools
        ]
        analysis.suggested_next_tools = valid_suggestions
        
        # Ensure confidence score is in valid range
        analysis.confidence_score = max(0.0, min(1.0, analysis.confidence_score))
        
        # If no valid tools suggested but followup needed, adjust
        if analysis.needs_followup and not analysis.suggested_next_tools:
            analysis.needs_followup = False
            analysis.reasoning += " (No valid follow-up tools available)"
        
        return result
    
    def batch_analyze(
        self,
        tool_results: List[dict]
    ) -> List[dspy.Prediction]:
        """
        Analyze multiple tool results in batch.
        
        Args:
            tool_results: List of dicts with tool execution information
            
        Returns:
            List of predictions with analyses
        """
        analyses = []
        
        for result_info in tool_results:
            analysis = self.forward(
                tool_name=result_info["tool_name"],
                tool_result=result_info["tool_result"],
                original_goal=result_info["original_goal"],
                available_tools=result_info["available_tools"],
                previous_tools_used=result_info.get("previous_tools_used", [])
            )
            analyses.append(analysis)
        
        return analyses