"""Multi-tool selector using dynamic Literal types.

This module demonstrates the proper DSPy pattern for multi-tool selection.
It uses type-safe dynamic signatures to eliminate string
parsing and provide robust multi-tool selection.
"""

__all__ = ['MultiToolSelector']

import dspy
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional

# Import shared models from the new module
from .models import MultiTool, MultiToolDecision, ToolCall


# Step 2: Dynamic Signature Factory
def create_multi_tool_signature(tool_names: tuple[str, ...]):
    """Create a signature with dynamic Literal types for multi-tool selection."""
    
    # Dynamic ToolCall with Literal constraint
    class DynamicToolCall(BaseModel):
        tool_name: Literal[tool_names]  # Type-safe tool names!
        arguments: Dict[str, Any] = Field(default_factory=dict)
    
    class DynamicMultiToolSignature(dspy.Signature):
        """
        Select one or more tools to fulfill the user's request.
        
        Steps:
        1. Understand the user's goal
        2. Identify which tools are needed
        3. Determine the order of execution
        4. Extract arguments for each tool
        
        Rules:
        - Select only the necessary tools
        - Order matters - tools should be in execution order
        - Extract all required arguments from the user's request
        - If arguments are missing, note it in the reasoning
        """
        # Inputs
        user_request: str = dspy.InputField(desc="What the user wants to do")
        available_tools: str = dspy.InputField(desc="Available tools with descriptions")
        
        # Outputs (properly typed!)
        tool_calls: List[DynamicToolCall] = dspy.OutputField(
            desc="List of tools to call in order with their arguments"
        )
        reasoning: str = dspy.OutputField(
            desc="Explanation of why these tools were selected and how they fulfill the request"
        )
    
    return DynamicMultiToolSignature


# Step 3: Simple Multi-Tool Selector
class MultiToolSelector(dspy.Module):
    """Multi-tool selector using dynamic Literal types - no string parsing needed!"""
    
    def __init__(self, use_predict: bool = False):
        """Initialize the selector.
        
        Args:
            use_predict: If True, use Predict instead of ChainOfThought
        """
        super().__init__()
        self._use_predict = use_predict
        self._signature_class = None
        self._selector = None
    
    def _ensure_initialized(self, tool_names: tuple[str, ...]):
        """Lazy initialization with tool names."""
        if self._selector is None:
            self._signature_class = create_multi_tool_signature(tool_names)
            if self._use_predict:
                self._selector = dspy.Predict(self._signature_class)
            else:
                self._selector = dspy.ChainOfThought(self._signature_class)
    
    def forward(self, user_request: str, available_tools: List[MultiTool]) -> MultiToolDecision:
        """Select multiple tools based on user request.
        
        Args:
            user_request: What the user wants to do
            available_tools: List of available MultiTool objects
            
        Returns:
            MultiToolDecision with type-safe tool calls
        """
        # Extract tool names for dynamic signature
        tool_names = tuple(tool.name.value for tool in available_tools)
        self._ensure_initialized(tool_names)
        
        # Format tools for the prompt
        tools_description = self._format_tools(available_tools)
        
        # Let DSPy handle everything - no manual parsing!
        result = self._selector(
            user_request=user_request,
            available_tools=tools_description
        )
        
        # Convert DynamicToolCall instances to ToolCall instances
        tool_calls = [
            ToolCall(
                tool_name=tc.tool_name,
                arguments=tc.arguments
            )
            for tc in result.tool_calls
        ]
        
        # Return the decision model
        return MultiToolDecision(
            tool_calls=tool_calls,
            reasoning=result.reasoning
        )
    
    def _format_tools(self, tools: List[MultiTool]) -> str:
        """Format tools in a clear, structured way."""
        lines = []
        
        # Group by category for better organization
        by_category = {}
        for tool in tools:
            category = tool.category
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(tool)
        
        # Format each category
        for category, category_tools in sorted(by_category.items()):
            lines.append(f"\n{category.upper()} TOOLS:")
            for tool in sorted(category_tools, key=lambda t: t.name.value):
                # Format arguments
                if tool.arguments:
                    args = ", ".join([
                        f"{arg.name} ({arg.type})"
                        for arg in tool.arguments
                    ])
                    args_str = f" - Args: {args}"
                else:
                    args_str = " - No arguments"
                
                lines.append(f"- {tool.name.value}: {tool.description}{args_str}")
        
        return "\n".join(lines).strip()


