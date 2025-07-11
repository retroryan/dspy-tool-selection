"""Tool sets for grouping related tools."""
from typing import List, Optional, Dict
from importlib import import_module
from pydantic import BaseModel, Field, ConfigDict

from .base_tool import ToolTestCase


class ToolSetTestCase(ToolTestCase):
    """Extended test case for tool sets."""
    tool_set: str  # Which tool set this test belongs to
    scenario: Optional[str] = None  # Optional scenario grouping


class ToolSetConfig(BaseModel):
    """Configuration for a tool set using Pydantic."""
    model_config = ConfigDict(frozen=True)  # Immutable configuration
    
    name: str
    description: str
    tool_modules: List[str]


class ToolSet(BaseModel):
    """Tool set with Pydantic validation."""
    config: ToolSetConfig
    
    def load(self) -> None:
        """Load all tools in this set."""
        for module_path in self.config.tool_modules:
            import_module(module_path)
    
    def get_loaded_tools(self) -> List[str]:
        """Get names of tools that should be loaded by this set."""
        # Extract tool names from module paths
        tool_names = []
        for module in self.config.tool_modules:
            # Assuming module name matches tool name (e.g., "tool_selection.tools.treasure_hunt.give_hint" -> "give_hint")
            tool_name = module.split('.')[-1]
            tool_names.append(tool_name)
        return tool_names
    
    @classmethod
    def get_test_cases(cls) -> List[ToolSetTestCase]:
        """Return test cases - must be implemented by subclasses."""
        return []


# Define specific tool sets
class TreasureHuntToolSet(ToolSet):
    """Tool set for treasure hunting game."""
    
    def __init__(self):
        super().__init__(
            config=ToolSetConfig(
                name="treasure_hunt",
                description="Simple treasure hunting game tools",
                tool_modules=[
                    "tool_selection.tools.treasure_hunt.give_hint",
                    "tool_selection.tools.treasure_hunt.guess_location"
                ]
            )
        )
    
    @classmethod
    def get_test_cases(cls) -> List[ToolSetTestCase]:
        """Return test cases for treasure hunt scenarios."""
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
                expected_tools=["give_hint", "guess_location"],
                description="Multi-tool treasure hunt",
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
    """Tool set for productivity tools."""
    
    def __init__(self):
        super().__init__(
            config=ToolSetConfig(
                name="productivity",
                description="Productivity and task management tools",
                tool_modules=[
                    "tool_selection.tools.productivity.set_reminder"
                ]
            )
        )
    
    @classmethod
    def get_test_cases(cls) -> List[ToolSetTestCase]:
        """Return test cases for productivity scenarios."""
        return [
            ToolSetTestCase(
                request="Remind me to submit the report at 5pm",
                expected_tools=["set_reminder"],
                description="Work reminder",
                tool_set="productivity",
                scenario="work"
            ),
            ToolSetTestCase(
                request="Set multiple reminders for my tasks today",
                expected_tools=["set_reminder"],
                description="Multiple reminders",
                tool_set="productivity",
                scenario="planning"
            )
        ]


# Tool set registry with validation
class ToolSetRegistry(BaseModel):
    """Registry for tool sets with validation."""
    tool_sets: Dict[str, ToolSet] = Field(default_factory=dict)
    
    def register(self, tool_set: ToolSet) -> None:
        """Register a tool set."""
        self.tool_sets[tool_set.config.name] = tool_set
    
    def load_tool_set(self, name: str) -> ToolSet:
        """Load a specific tool set by name."""
        if name not in self.tool_sets:
            raise ValueError(f"Unknown tool set: {name}. Available: {list(self.tool_sets.keys())}")
        
        tool_set = self.tool_sets[name]
        tool_set.load()
        return tool_set
    
    def get_all_tool_sets(self) -> Dict[str, ToolSet]:
        """Get all registered tool sets."""
        return self.tool_sets.copy()
    
    def get_test_cases(self, name: str) -> List[ToolSetTestCase]:
        """Get test cases for a specific tool set."""
        if name not in self.tool_sets:
            raise ValueError(f"Unknown tool set: {name}")
        
        tool_set_class = type(self.tool_sets[name])
        return tool_set_class.get_test_cases()
    
    def get_all_test_cases(self) -> List[ToolSetTestCase]:
        """Get test cases from all tool sets."""
        all_test_cases = []
        for tool_set in self.tool_sets.values():
            tool_set_class = type(tool_set)
            all_test_cases.extend(tool_set_class.get_test_cases())
        return all_test_cases


# Create and populate registry
tool_set_registry = ToolSetRegistry()
tool_set_registry.register(TreasureHuntToolSet())
tool_set_registry.register(ProductivityToolSet())