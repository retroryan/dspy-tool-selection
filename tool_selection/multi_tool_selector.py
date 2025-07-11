"""DSPy module for multi-tool selection with dynamic Literal types.

This module implements tool selection using DSPy's native Pydantic support
with dynamic signature generation for compile-time type safety.
"""

import dspy
from typing import List, Dict, Any, Optional, Literal, Type
from pydantic import BaseModel, Field

from .models import MultiToolDecision, ToolCall
from .base_tool import BaseTool, ToolArgument


class ToolInfo(BaseModel):
    """Information about an available tool."""
    name: str = Field(..., description="Tool identifier")
    description: str = Field(..., description="What the tool does")
    arguments: List[ToolArgument] = Field(default_factory=list, description="Tool arguments")


def create_dynamic_tool_signature(tool_names: tuple[str, ...]) -> Type[dspy.Signature]:
    """Create a signature with dynamic Literal types for compile-time type safety.
    
    This factory function generates a DSPy signature that constrains tool selection
    to only the available tools, providing type safety at the signature level.
    
    Args:
        tool_names: Tuple of available tool names
        
    Returns:
        A dynamically created signature class with Literal type constraints
    """
    
    # Create dynamic ToolSelection model with Literal constraint
    class DynamicToolSelection(BaseModel):
        """A tool selection with compile-time type safety."""
        tool_name: Literal[tool_names]  # Type-safe tool names!
        arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool")
        confidence: float = Field(ge=0, le=1, description="Confidence in this selection (0-1)")
    
    # Create the dynamic signature
    class DynamicMultiToolSignature(dspy.Signature):
        """Select multiple tools to accomplish a user's request.
        
        Analyze the request and select the appropriate tools with their arguments.
        Consider tool capabilities, required arguments, and how tools might work together.
        Only select from the available tools provided.
        """
        
        # DSPy Signatures define the input/output behavior of a DSPy module.
        # They are essentially a contract for the language model.
        # InputField and OutputField specify the role and description of each field.
        
        # Inputs
        user_request: str = dspy.InputField(
            desc="The user's request that may require one or more tools to accomplish"
        )
        available_tools: List[ToolInfo] = dspy.InputField(
            desc="List of available tools with their descriptions and required arguments"
        )
        
        # Outputs with dynamic type constraints
        # DSPy leverages Pydantic models to enforce structured outputs from the LM.
        # The Literal type ensures only valid tool names can be selected.
        reasoning: str = dspy.OutputField(
            desc="Step-by-step analysis of which tools are needed and why"
        )
        selected_tools: List[DynamicToolSelection] = dspy.OutputField(
            desc="List of selected tools with their arguments and confidence scores"
        )
        execution_order_matters: bool = dspy.OutputField(
            desc="Whether the order of tool execution is important",
            default=False
        )
    
    return DynamicMultiToolSignature


class MultiToolSelector(dspy.Module):
    """
    DSPy module for multi-tool selection with dynamic type safety.

    This module is responsible for taking a user's request and a list of available tools,
    then using a language model (via DSPy) to decide which tools to call and with what arguments.
    It dynamically generates DSPy signatures to ensure type safety based on the available tools.
    """
    
    def __init__(self, use_chain_of_thought: bool = True, max_tools: int = 5):
        """
        Initializes the MultiToolSelector module.

        Args:
            use_chain_of_thought (bool): If True, the selector will use DSPy's ChainOfThought
                                         predictor for more elaborate reasoning. If False,
                                         it will use a simpler DSPy.Predict.
            max_tools (int): The maximum number of tools the selector is allowed to choose
                             in a single decision. This helps to constrain the output.
        """
        super().__init__()  # Always call super().__init__() as per DSPy best practices
        
        self.max_tools = max_tools  # Store the maximum number of tools to select
        self.use_chain_of_thought = use_chain_of_thought  # Store the CoT preference
        self._signature_cache = {}  # Cache for dynamically generated DSPy signatures
        
    def _get_or_create_signature(self, tool_names: tuple[str, ...]) -> Type[dspy.Signature]:
        """Get cached signature or create new one for given tools.
        
        This ensures we reuse signatures for the same set of tools,
        improving performance and consistency.
        """
        cache_key = tool_names
        if cache_key not in self._signature_cache:
            self._signature_cache[cache_key] = create_dynamic_tool_signature(tool_names)
        return self._signature_cache[cache_key]
    
    def forward(self, request: str, tools: List[BaseTool]) -> MultiToolDecision:
        """Select tools based on user request with compile-time type safety.
        
        The `forward` method defines the logic of the DSPy module.
        When this module is called, the `forward` method is executed.
        It takes inputs, uses the defined predictors, and returns the output.
        
        Args:
            request: The user's request
            tools: Available BaseTool instances
            
        Returns:
            MultiToolDecision with selected tools and reasoning
        """
        # Extract tool names for dynamic signature
        tool_names = tuple(tool.name for tool in tools)
        tool_map = {tool.name: tool for tool in tools}
        
        # Convert BaseTool instances to ToolInfo
        tool_infos = []
        for tool in tools:
            tool_infos.append(ToolInfo(
                name=tool.name,
                description=tool.description,
                arguments=tool.arguments
            ))
        
        # Get or create dynamic signature for these specific tools
        DynamicSignature = self._get_or_create_signature(tool_names)
        
        # Create predictor with dynamic signature
        # dspy.ChainOfThought encourages step-by-step reasoning
        # dspy.Predict is a basic predictor for direct generation
        if self.use_chain_of_thought:
            predictor = dspy.ChainOfThought(DynamicSignature)
        else:
            predictor = dspy.Predict(DynamicSignature)
        
        # Execute with type-safe signature
        # The dynamic Literal type ensures only valid tool names can be selected
        result = predictor(
            user_request=request,
            available_tools=tool_infos
        )
        
        # Convert selections to ToolCall objects
        # The dynamic Literal type ensures tool_name is always valid
        valid_selections = []
        for selection in result.selected_tools[:self.max_tools]:
            # Tool name is guaranteed to be valid by Literal type
            tool = tool_map[selection.tool_name]
            
            # Validate arguments using the tool's args_model if available
            arguments = selection.arguments
            if tool.args_model:
                try:
                    validated = tool.args_model(**arguments)
                    arguments = validated.model_dump()
                except Exception:
                    # Keep original arguments if validation fails
                    pass
            
            valid_selections.append(ToolCall(
                tool_name=selection.tool_name,
                arguments=arguments
            ))
        
        return MultiToolDecision(
            reasoning=result.reasoning,
            tool_calls=valid_selections
        )