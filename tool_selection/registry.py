"""Central registry for all tools."""
from typing import Dict, Type, Callable, List, Optional, Any
from .base_tool import BaseTool


class ToolRegistry:
    """
    A central registry for managing and accessing all available tools in the system.

    This class provides methods to register new tool classes, retrieve tool instances
    by name, execute tools with given arguments, and manage test cases associated
    with registered tools. It ensures that tool names are unique and provides a
    single point of access for tool management.
    """
    
    def __init__(self):
        """Initializes the ToolRegistry with empty dictionaries for tools and instances."""
        self._tools: Dict[str, Type[BaseTool]] = {}  # Stores tool classes, keyed by tool name
        self._instances: Dict[str, BaseTool] = {}  # Stores instantiated tool objects, keyed by tool name
    
    def register(self, tool_class: Type[BaseTool]) -> None:
        """
        Registers a new tool class with the registry.

        Upon registration, an instance of the tool is created and cached.
        Ensures that tool names are unique to prevent conflicts.

        Args:
            tool_class (Type[BaseTool]): The tool class to register. Must be a subclass of BaseTool.

        Raises:
            ValueError: If a tool with the same name is already registered.
        """
        # Validation of NAME and MODULE happens in BaseTool.__init_subclass__
        tool_name = tool_class.NAME
        
        if tool_name in self._tools:
            raise ValueError(f"Tool '{tool_name}' is already registered.")
        
        self._tools[tool_name] = tool_class
        
        # Create and cache tool instance. Tools are Pydantic models.
        instance = tool_class()
        self._instances[tool_name] = instance
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Retrieves a tool instance by its name.

        Args:
            name (str): The name of the tool to retrieve.

        Returns:
            Optional[BaseTool]: The tool instance if found, otherwise None.
        """
        return self._instances.get(name)
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """
        Retrieves all registered tool instances.

        Returns:
            Dict[str, BaseTool]: A dictionary of all registered tool instances, keyed by their names.
        """
        return self._instances.copy()
    
    def get_tool_names(self) -> List[str]:
        """
        Retrieves a list of names of all registered tools.

        Returns:
            List[str]: A list containing the names of all registered tools.
        """
        return list(self._tools.keys())
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Executes a registered tool by its name with the given arguments.

        Args:
            tool_name (str): The name of the tool to execute.
            **kwargs: Arbitrary keyword arguments to pass to the tool's execute method.
                      These arguments will be validated by the tool's args_model if defined.

        Returns:
            Dict[str, Any]: The result of the tool's execution.

        Raises:
            ValueError: If the specified tool is not found in the registry.
        """
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        # Use the tool's validate_and_execute method for argument validation and execution
        return tool.validate_and_execute(**kwargs)
    
    
    def get_all_test_cases(self) -> List[Any]:
        """
        Collects and returns all test cases defined across all registered tools.

        This method dynamically looks for a 'get_test_cases' method on each registered
        tool class and aggregates their test cases.

        Returns:
            List[Any]: A list of all collected test cases.
        """
        # Import here to avoid circular dependency issues, as ToolTestCase might depend on registry
        from .base_tool import ToolTestCase
        
        test_cases = []
        for tool_class in self._tools.values():
            # Check if the tool class has a method to provide test cases
            if hasattr(tool_class, 'get_test_cases'):
                test_cases.extend(tool_class.get_test_cases()) # type: ignore
        return test_cases
    
    def clear(self) -> None:
        """
        Clears all registered tools and their instances from the registry.

        This is primarily useful for testing scenarios to ensure a clean state.
        """
        self._tools.clear()
        self._instances.clear()


# Global registry instance
# This instance is used throughout the application to interact with the tool registry.
registry = ToolRegistry()


def register_tool(cls: Type[BaseTool]) -> Type[BaseTool]:
    """
    A decorator to automatically register a tool class with the global ToolRegistry.

    This simplifies the process of adding new tools to the system by allowing
    them to be registered simply by decorating their class definition.

    Args:
        cls (Type[BaseTool]): The tool class to be registered.

    Returns:
        Type[BaseTool]: The decorated tool class, unchanged.
    """
    registry.register(cls)
    return cls