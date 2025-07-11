"""
Tool sets for grouping related tools.

This module defines a system for organizing tools into logical groups (tool sets).
Each tool set can contain multiple tools and provides a way to manage and load
collections of tools relevant to specific domains or functionalities.
It also includes an extended test case model for tool set-specific testing.
"""
from typing import List, Optional, Dict, Type, ClassVar
from pydantic import BaseModel, Field, ConfigDict

from .base_tool import ToolTestCase, BaseTool


class ToolSetTestCase(ToolTestCase):
    """
    Extends the base ToolTestCase to include tool set-specific metadata.

    This allows test cases to be associated with a particular tool set and
    optionally a scenario within that set, aiding in more organized testing.
    """
    tool_set: str  # The name of the tool set this test case belongs to
    scenario: Optional[str] = None  # An optional, more granular grouping for test cases within a tool set


class ToolSetConfig(BaseModel):
    """
    Configuration model for a ToolSet.

    This model defines the immutable properties of a tool set, such as its name,
    description, and the list of tool classes it contains.
    """
    model_config = ConfigDict(frozen=True)  # Ensures the configuration is immutable after creation
    
    name: str  # The unique name of the tool set (e.g., "treasure_hunt", "productivity")
    description: str  # A brief description of the tool set's purpose
    tool_classes: List[Type[BaseTool]]  # A list of direct references to the BaseTool subclasses included in this set


class ToolSet(BaseModel):
    """
    Base class for defining a collection of related tools.

    Subclasses should define their specific tools and provide test cases relevant
    to their domain. This class handles the loading of its contained tools into
    the global tool registry.
    """
    config: ToolSetConfig  # The immutable configuration for this tool set
    
    def load(self) -> None:
        """
        Registers all tool classes defined in this tool set's configuration
        with the global tool registry.

        Tools are only registered if they are not already present in the registry,
        preventing duplicate registrations.
        """
        from tool_selection.registry import registry  # Import here to avoid circular dependency
        for tool_class in self.config.tool_classes:
            # Only register the tool if it hasn't been registered already
            if not registry.get_tool(tool_class.NAME):
                registry.register(tool_class)
    
    def get_loaded_tools(self) -> List[str]:
        """
        Returns a list of names of the tools that are part of this tool set.

        These are the tools that *should* be loaded into the registry when this
        tool set is activated.
        """
        return [tool_class.NAME for tool_class in self.config.tool_classes]
    
    @classmethod
    def get_test_cases(cls) -> List[ToolSetTestCase]:
        """
        Abstract method to be implemented by subclasses.

        Subclasses should return a list of `ToolSetTestCase` objects that are
        specific to the functionality provided by the tools within that set.

        Returns:
            List[ToolSetTestCase]: A list of test cases for the tool set.
        """
        return []


# Define specific tool sets by subclassing ToolSet
class TreasureHuntToolSet(ToolSet):
    """
    A specific tool set for tools related to a treasure hunting game.

    This set includes tools like `GiveHintTool` and `GuessLocationTool`.
    """
    NAME: ClassVar[str] = "treasure_hunt"  # The unique name for this tool set
    
    def __init__(self):
        """
        Initializes the TreasureHuntToolSet, defining its name, description,
        and the specific tool classes it encompasses.
        """
        # Lazy import tool classes to avoid circular dependencies and ensure tools are registered only when needed
        from tools.treasure_hunt.give_hint import GiveHintTool
        from tools.treasure_hunt.guess_location import GuessLocationTool
        
        super().__init__(
            config=ToolSetConfig(
                name=self.NAME,
                description="Simple treasure hunting game tools",
                tool_classes=[
                    GiveHintTool,
                    GuessLocationTool
                ]
            )
        )
    
    @classmethod
    def get_test_cases(cls) -> List[ToolSetTestCase]:
        """
        Returns a predefined list of test cases for treasure hunt scenarios.

        These cases cover various interactions with the treasure hunt tools,
        including single and multi-tool requests.
        """
        return [
            ToolSetTestCase(
                request="I need help finding the treasure",
                expected_tools=["give_hint"],
                description="Initial treasure hunt help",
                tool_set="treasure_hunt"
            ),
            ToolSetTestCase(
                request="I think the treasure is at the library",
                expected_tools=["guess_location"],
                description="Guessing treasure location",
                tool_set="treasure_hunt"
            ),
            ToolSetTestCase(
                request="Give me a hint and I'll guess where it is",
                expected_tools=["give_hint"],
                description="Request for hint before guessing",
                tool_set="treasure_hunt"
            ),
            ToolSetTestCase(
                request="Help me find the treasure and I'll try to guess",
                expected_tools=["give_hint", "guess_location"],
                description="Alternative multi-tool request",
                tool_set="treasure_hunt"
            )
        ]


class ProductivityToolSet(ToolSet):
    """
    A specific tool set for productivity and task management tools.

    This set currently includes the `SetReminderTool`.
    """
    NAME: ClassVar[str] = "productivity"  # The unique name for this tool set
    
    def __init__(self):
        """
        Initializes the ProductivityToolSet, defining its name, description,
        and the specific tool classes it encompasses.
        """
        # Lazy import tool classes
        from tools.productivity.set_reminder import SetReminderTool
        
        super().__init__(
            config=ToolSetConfig(
                name=self.NAME,
                description="Productivity and task management tools",
                tool_classes=[
                    SetReminderTool
                ]
            )
        )
    
    @classmethod
    def get_test_cases(cls) -> List[ToolSetTestCase]:
        """
        Returns a predefined list of test cases for productivity scenarios.

        These cases cover various interactions with productivity tools, such as
        setting reminders.
        """
        return [
            ToolSetTestCase(
                request="Remind me to submit the report at 5pm",
                expected_tools=["set_reminder"],
                description="Work reminder",
                tool_set="productivity",
                scenario="work"
            ),
            ToolSetTestCase(
                request="Set  a reminder for my meeting tomorrow at 10am and another for lunch at 1pm",
                expected_tools=["set_reminder"],
                description="Multiple reminders",
                tool_set="productivity",
                scenario="planning"
            )
        ]


class ToolSetRegistry(BaseModel):
    """
    A central registry for managing and loading different tool sets.

    This registry allows for dynamic loading and unloading of tool sets,
    ensuring that only the necessary tools are available at any given time.
    It also provides methods to retrieve test cases from registered tool sets.
    """
    tool_sets: Dict[str, ToolSet] = Field(default_factory=dict)  # Stores registered ToolSet instances, keyed by name
    
    def register(self, tool_set: ToolSet) -> None:
        """
        Registers a new tool set with the registry.

        Args:
            tool_set (ToolSet): The tool set instance to register.
        """
        self.tool_sets[tool_set.config.name] = tool_set
    
    def load_tool_set(self, name: str) -> ToolSet:
        """
        Loads a specific tool set by name into the global tool registry.

        This method first clears the existing global tool registry to ensure
        that only the tools from the specified tool set are active.

        Args:
            name (str): The name of the tool set to load.

        Returns:
            ToolSet: The loaded tool set instance.

        Raises:
            ValueError: If the specified tool set is not found in the registry.
        """
        from tool_selection.registry import registry  # Import here to avoid circular dependency
        
        if name not in self.tool_sets:
            raise ValueError(f"Unknown tool set: {name}. Available: {list(self.tool_sets.keys())}")
        
        # Clear the global tool registry to ensure a clean slate before loading new tools
        registry.clear()
        
        tool_set = self.tool_sets[name]
        tool_set.load()  # Load tools from this tool set into the global registry
        return tool_set
    
    def get_all_tool_sets(self) -> Dict[str, ToolSet]:
        """
        Returns a copy of all registered tool sets.

        Returns:
            Dict[str, ToolSet]: A dictionary of all registered tool sets, keyed by their names.
        """
        return self.tool_sets.copy()
    
    def get_test_cases(self, name: str) -> List[ToolSetTestCase]:
        """
        Retrieves test cases for a specific tool set.

        Args:
            name (str): The name of the tool set.

        Returns:
            List[ToolSetTestCase]: A list of test cases associated with the specified tool set.

        Raises:
            ValueError: If the specified tool set is not found.
        """
        if name not in self.tool_sets:
            raise ValueError(f"Unknown tool set: {name}")
        
        # Ensure the tool set's tools are loaded before attempting to get test cases
        self.tool_sets[name].load()
        tool_set_class = type(self.tool_sets[name])
        return tool_set_class.get_test_cases()
    
    def get_all_test_cases(self) -> List[ToolSetTestCase]:
        """
        Aggregates and returns all test cases from all registered tool sets.

        Returns:
            List[ToolSetTestCase]: A combined list of all test cases.
        """
        all_test_cases = []
        for tool_set in self.tool_sets.values():
            tool_set_class = type(tool_set)
            all_test_cases.extend(tool_set_class.get_test_cases())
        return all_test_cases


# Global tool set registry instance
# This instance is used throughout the application to manage and access tool sets.
tool_set_registry = ToolSetRegistry()

# Register default tool sets upon import to make them immediately available
tool_set_registry.register(TreasureHuntToolSet())
tool_set_registry.register(ProductivityToolSet())
