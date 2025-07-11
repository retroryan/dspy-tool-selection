"""
Shared data models for tool selection and registry.

This module contains the shared Pydantic models used by the tool selector,
defining the structure for tool invocations and the overall decision output.
These models are crucial for consistent data exchange within the tool selection
process.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """
    Represents a single invocation of a tool with its specified arguments.

    This model is used to structure the output of the tool selection process,
    indicating which tool should be called and with what parameters.
    """
    tool_name: str = Field(..., description="The unique name of the tool to be called (e.g., 'set_reminder')")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="A dictionary of arguments to pass to the tool, where keys are argument names and values are their corresponding values.")


class MultiToolDecision(BaseModel):
    """
    Represents the comprehensive decision made by the tool selector.

    This model encapsulates the reasoning behind the tool selection and a list
    of one or more tool calls that should be executed to fulfill the user's request.
    """
    reasoning: str = Field(..., description="A detailed explanation or step-by-step thought process behind why the specific tools were selected and how they address the user's request.")
    tool_calls: List[ToolCall] = Field(..., description="A list of ToolCall objects, each representing a tool to be invoked. The order of tools in this list may or may not be significant depending on the 'execution_order_matters' flag in the signature.")