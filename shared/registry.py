"""Central registry for all tools adapted for agentic loop integration."""
import time
from typing import Dict, Type, Callable, List, Optional, Any
from .models import ToolExecutionResult, ToolCall
from tool_selection.base_tool import BaseTool


class ToolRegistry:
    """
    A central registry for managing and accessing all available tools in the system.

    This class provides methods to register new tool classes, retrieve tool instances
    by name, execute tools with given arguments, and manage test cases associated
    with registered tools. It ensures that tool names are unique and provides a
    single point of access for tool management.
    
    Updated for agentic loop integration to return ToolExecutionResult objects.
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
    
    def execute_tool(self, tool_call: ToolCall) -> ToolExecutionResult:
        """
        Executes a registered tool by ToolCall and returns ToolExecutionResult.

        Args:
            tool_call (ToolCall): The tool call containing tool name and arguments.

        Returns:
            ToolExecutionResult: The result of the tool's execution with metadata.
        """
        start_time = time.time()
        
        try:
            tool = self.get_tool(tool_call.tool_name)
            if not tool:
                return ToolExecutionResult(
                    tool_name=tool_call.tool_name,
                    success=False,
                    result=None,
                    error=f"Unknown tool: {tool_call.tool_name}",
                    execution_time=time.time() - start_time,
                    parameters=tool_call.arguments
                )
            
            # Use the tool's validate_and_execute method for argument validation and execution
            result = tool.validate_and_execute(**tool_call.arguments)
            
            return ToolExecutionResult(
                tool_name=tool_call.tool_name,
                success=True,
                result=result,
                error=None,
                execution_time=time.time() - start_time,
                parameters=tool_call.arguments
            )
            
        except Exception as e:
            return ToolExecutionResult(
                tool_name=tool_call.tool_name,
                success=False,
                result=None,
                error=str(e),
                execution_time=time.time() - start_time,
                parameters=tool_call.arguments
            )
    
    def execute_tool_legacy(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility - executes a tool by name with arguments.

        Args:
            tool_name (str): The name of the tool to execute.
            **kwargs: Arbitrary keyword arguments to pass to the tool's execute method.

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
        # Import here to avoid circular dependency issues
        from tool_selection.base_tool import ToolTestCase
        
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


# No global registry instance - all registration is explicit