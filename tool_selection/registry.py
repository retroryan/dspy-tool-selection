"""Central registry for all tools with type-safe operations."""
from typing import Dict, List, Type, Optional, TypeVar, Any
from .base_tool import BaseTool, ToolTestCase

T = TypeVar('T', bound=BaseTool)


class ToolRegistry:
    """Central registry for all tools with type-safe operations."""
    
    def __init__(self):
        self._tool_classes: Dict[str, Type[BaseTool]] = {}
        self._instances: Dict[str, BaseTool] = {}
    
    def register(self, tool_class: Type[BaseTool]) -> None:
        """Register a tool class."""
        # Create a temporary instance to get metadata
        temp_instance = tool_class()
        tool_name = tool_class.metadata.name
        
        self._tool_classes[tool_name] = tool_class
        self._instances[tool_name] = temp_instance
    
    def get_tool(self, name: str, tool_type: Type[T] = BaseTool) -> Optional[T]:
        """Get a tool instance by name with type checking."""
        tool = self._instances.get(name)
        if tool and isinstance(tool, tool_type):
            return tool
        return None
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """Get all registered tools."""
        return self._instances.copy()
    
    def get_tools_by_category(self, category: str) -> Dict[str, BaseTool]:
        """Get tools filtered by category."""
        return {
            name: tool for name, tool in self._instances.items()
            if tool.metadata.category == category
        }
    
    def get_tool_names(self) -> List[str]:
        """Get all registered tool names."""
        return list(self._tool_classes.keys())
    
    def get_all_test_cases(self) -> List[ToolTestCase]:
        """Get test cases from all registered tools."""
        test_cases = []
        for tool_class in self._tool_classes.values():
            test_cases.extend(tool_class.get_test_cases())
        return test_cases
    
    def execute_tool(self, name: str, **kwargs) -> Any:
        """Execute a tool with automatic validation."""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")
        
        # Use the tool's validate_and_execute method
        return tool.validate_and_execute(**kwargs)
    
    def clear(self) -> None:
        """Clear all registered tools (useful for testing)."""
        self._tool_classes.clear()
        self._instances.clear()


# Global registry instance
registry = ToolRegistry()


def register_tool(tool_class: Type[BaseTool]) -> Type[BaseTool]:
    """Decorator to register a tool."""
    registry.register(tool_class)
    return tool_class