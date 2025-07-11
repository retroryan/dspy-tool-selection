"""
Tool selection module for DSPy multi-tool demonstrations.

This package provides the core components for defining, registering, and selecting
tools within a DSPy application, especially for scenarios requiring multiple tool calls.
"""

from .multi_tool_selector import MultiToolSelector
from .registry import registry
from .models import (
    MultiToolDecision,
    ToolCall
)
from .base_tool import BaseTool, ToolTestCase

# Define the public API of the tool_selection module
__all__ = [
    'MultiToolSelector',  # Main class for selecting multiple tools
    'registry',           # Global tool registry instance
    'MultiToolDecision',  # Pydantic model for the decision output of the tool selector
    'ToolCall',           # Pydantic model for a single tool invocation
    'BaseTool',           # Base class for all tools
    'ToolTestCase'        # Pydantic model for defining tool test cases
]