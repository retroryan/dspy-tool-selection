"""
Tool set registry for explicit tool registration and management.

This module provides a registry system for managing tool sets, allowing
explicit control over which tools are available in the system.
"""

from typing import Dict, List, Optional
from .registry import ToolRegistry
from .models import ToolExecutionResult, ToolCall


class ToolSetRegistry:
    """
    A registry that manages tool sets and provides tool execution capabilities.
    
    This registry wraps a ToolRegistry and provides methods for managing
    tool sets while maintaining explicit control over tool registration.
    """
    
    def __init__(self):
        """Initialize the registry with an empty tool registry."""
        self._tool_registry = ToolRegistry()
        self._loaded_tool_sets: Dict[str, str] = {}  # tool_set_name -> description
    
    def register_tool_set(self, tool_set_name: str, description: str, tool_classes: List[type]) -> None:
        """
        Register a tool set with its tools.
        
        Args:
            tool_set_name: Name of the tool set (e.g., "treasure_hunt")
            description: Description of the tool set
            tool_classes: List of tool classes to register
        """
        # Clear existing tools first
        self._tool_registry.clear()
        
        # Register all tools in the set
        for tool_class in tool_classes:
            self._tool_registry.register(tool_class)
        
        # Track the loaded tool set
        self._loaded_tool_sets[tool_set_name] = description
    
    def get_tool_names(self) -> List[str]:
        """Get names of all currently registered tools."""
        return self._tool_registry.get_tool_names()
    
    def execute_tool(self, tool_call: ToolCall) -> ToolExecutionResult:
        """Execute a tool and return the result."""
        return self._tool_registry.execute_tool(tool_call)
    
    def get_loaded_tool_sets(self) -> Dict[str, str]:
        """Get currently loaded tool sets."""
        return self._loaded_tool_sets.copy()
    
    def clear(self) -> None:
        """Clear all registered tools and tool sets."""
        self._tool_registry.clear()
        self._loaded_tool_sets.clear()


def create_tool_set_registry() -> ToolSetRegistry:
    """
    Creates and populates a tool set registry with available tool sets.
    
    Returns:
        ToolSetRegistry: A configured registry with tool sets registered
    """
    registry = ToolSetRegistry()
    
    # Import tool sets here to avoid circular dependencies
    from tool_selection.tool_sets import TreasureHuntToolSet, ProductivityToolSet, EcommerceToolSet
    
    # Register treasure hunt tool set by default
    treasure_hunt = TreasureHuntToolSet()
    registry.register_tool_set(
        tool_set_name="treasure_hunt",
        description=treasure_hunt.config.description,
        tool_classes=treasure_hunt.config.tool_classes
    )
    
    return registry


def create_ecommerce_tool_set_registry() -> ToolSetRegistry:
    """
    Creates and populates a tool set registry with ecommerce tools.
    
    Returns:
        ToolSetRegistry: A configured registry with ecommerce tools
    """
    registry = ToolSetRegistry()
    
    # Import tool sets here to avoid circular dependencies
    from tool_selection.tool_sets import EcommerceToolSet
    
    # Register ecommerce tool set
    ecommerce = EcommerceToolSet()
    registry.register_tool_set(
        tool_set_name="ecommerce",
        description=ecommerce.config.description,
        tool_classes=ecommerce.config.tool_classes
    )
    
    return registry


def create_productivity_tool_set_registry() -> ToolSetRegistry:
    """
    Creates and populates a tool set registry with productivity tools.
    
    Returns:
        ToolSetRegistry: A configured registry with productivity tools
    """
    registry = ToolSetRegistry()
    
    # Import tool sets here to avoid circular dependencies
    from tool_selection.tool_sets import ProductivityToolSet
    
    # Register productivity tool set
    productivity = ProductivityToolSet()
    registry.register_tool_set(
        tool_set_name="productivity",
        description=productivity.config.description,
        tool_classes=productivity.config.tool_classes
    )
    
    return registry