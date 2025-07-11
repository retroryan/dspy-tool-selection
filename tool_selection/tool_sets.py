"""Tool sets for grouping related tools."""
from typing import List, Optional, Dict, Type, ClassVar
from pydantic import BaseModel, Field, ConfigDict

from .base_tool import ToolTestCase, BaseTool

# Import tool classes directly
from tools.treasure_hunt.give_hint import GiveHintTool
from tools.treasure_hunt.guess_location import GuessLocationTool
from tools.productivity.set_reminder import SetReminderTool


class ToolSetTestCase(ToolTestCase):
    """Extended test case for tool sets."""
    tool_set: str  # Which tool set this test belongs to
    scenario: Optional[str] = None  # Optional scenario grouping


class ToolSetConfig(BaseModel):
    """Configuration for a tool set using Pydantic."""
    model_config = ConfigDict(frozen=True)  # Immutable configuration
    
    name: str
    description: str
    tool_classes: List[Type[BaseTool]]  # Direct references to tool classes


class ToolSet(BaseModel):
    """Tool set with Pydantic validation."""
    config: ToolSetConfig
    
    def load(self) -> None:
        """Load all tools in this set."""
        # Tools are automatically registered when their classes are imported
        # Since we're importing the classes directly, they're already loaded
        pass
    
    def get_loaded_tools(self) -> List[str]:
        """Get names of tools that should be loaded by this set."""
        return [tool_class.NAME for tool_class in self.config.tool_classes]
    
    @classmethod
    def get_test_cases(cls) -> List[ToolSetTestCase]:
        """Return test cases - must be implemented by subclasses."""
        return []


# Define specific tool sets
class TreasureHuntToolSet(ToolSet):
    """Tool set for treasure hunting game."""
    NAME: ClassVar[str] = "treasure_hunt"
    
    def __init__(self):
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
    NAME: ClassVar[str] = "productivity"
    
    def __init__(self):
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
        
        # Ensure the tool set is loaded first
        self.tool_sets[name].load()
        tool_set_class = type(self.tool_sets[name])
        return tool_set_class.get_test_cases()
    
    def get_all_test_cases(self) -> List[ToolSetTestCase]:
        """Get test cases from all tool sets."""
        all_test_cases = []
        for tool_set in self.tool_sets.values():
            tool_set_class = type(tool_set)
            all_test_cases.extend(tool_set_class.get_test_cases())
        return all_test_cases


# Event management tool set
# TODO: Uncomment when event tools are updated with NAME/MODULE constants
# class EventsToolSet(ToolSet):
#     """Tool set for event management."""
#     NAME = "events"
#     
#     def __init__(self):
#         super().__init__(
#             config=ToolSetConfig(
#                 name=self.NAME,
#                 description="Event management and scheduling tools",
#                 tool_classes=[
#                     FindEventsTool,
#                     CreateEventTool,
#                     CancelEventTool
#                 ]
#             )
#         )
    
#     @classmethod
#     def get_test_cases(cls) -> List[ToolSetTestCase]:
#         """Return test cases for event scenarios."""
#         return [
#             ToolSetTestCase(
#                 request="Find concerts this weekend and create a reminder",
#                 expected_tools=["find_events", "set_reminder"],
#                 description="Multi-tool event planning",
#                 tool_set="events"
#             ),
#             ToolSetTestCase(
#                 request="Cancel all my events for tomorrow",
#                 expected_tools=["cancel_event"],
#                 description="Bulk cancellation",
#                 tool_set="events"
#             )
#         ]


# E-commerce tool set
# TODO: Uncomment when ecommerce tools are updated with NAME/MODULE constants
# class EcommerceToolSet(ToolSet):
#     """Tool set for e-commerce operations."""
#     NAME = "ecommerce"
#     
#     def __init__(self):
#         super().__init__(
#             config=ToolSetConfig(
#                 name=self.NAME,
#                 description="E-commerce and shopping tools",
#                 tool_classes=[
#                     SearchProductsTool,
#                     AddToCartTool,
#                     TrackOrderTool,
#                     ReturnItemTool
#                 ]
#             )
#         )
    
#     @classmethod
#     def get_test_cases(cls) -> List[ToolSetTestCase]:
#         """Return test cases for e-commerce scenarios."""
#         return [
#             ToolSetTestCase(
#                 request="Find electronics under $500 and add to cart",
#                 expected_tools=["search_products", "add_to_cart"],
#                 description="Shopping workflow",
#                 tool_set="ecommerce"
#             ),
#             ToolSetTestCase(
#                 request="Track my recent orders and return any damaged items",
#                 expected_tools=["track_order", "return_item"],
#                 description="Order management",
#                 tool_set="ecommerce"
#             )
#         ]


# Finance tool set
# TODO: Uncomment when finance tools are updated with NAME/MODULE constants
# class FinanceToolSet(ToolSet):
#     """Tool set for financial operations."""
#     NAME = "finance"
#     
#     def __init__(self):
#         super().__init__(
#             config=ToolSetConfig(
#                 name=self.NAME,
#                 description="Financial and banking tools",
#                 tool_classes=[
#                     CheckBalanceTool,
#                     TransferMoneyTool,
#                     PayBillTool,
#                     GetStatementTool,
#                     InvestTool
#                 ]
#             )
#         )
    
#     @classmethod
#     def get_test_cases(cls) -> List[ToolSetTestCase]:
#         """Return test cases for finance scenarios."""
#         return [
#             ToolSetTestCase(
#                 request="Check my balance and pay the electric bill",
#                 expected_tools=["check_balance", "pay_bill"],
#                 description="Balance check and bill payment",
#                 tool_set="finance"
#             ),
#             ToolSetTestCase(
#                 request="Transfer money to savings and invest the rest",
#                 expected_tools=["transfer_money", "invest"],
#                 description="Money management workflow",
#                 tool_set="finance"
#             ),
#             ToolSetTestCase(
#                 request="Get my statement and check all accounts",
#                 expected_tools=["get_statement", "check_balance"],
#                 description="Account review",
#                 tool_set="finance"
#             )
#         ]


# Multi-domain tool set for testing cross-domain scenarios
# TODO: Uncomment when all domain tools are updated
# class MultiDomainToolSet(ToolSet):
#     """Tool set combining tools from multiple domains."""
#     NAME = "multi_domain"
#     
#     def __init__(self):
#         super().__init__(
#             config=ToolSetConfig(
#                 name=self.NAME,
#                 description="Combined tools from all domains for complex workflows",
#                 tool_classes=[
#                     # Events
#                     FindEventsTool,
#                     CancelEventTool,
#                     # E-commerce
#                     SearchProductsTool,
#                     TrackOrderTool,
#                     # Finance
#                     CheckBalanceTool,
#                     PayBillTool,
#                     # Productivity
#                     SetReminderTool
#                 ]
#             )
#         )
    
#     @classmethod
#     def get_test_cases(cls) -> List[ToolSetTestCase]:
#         """Return test cases for multi-domain scenarios."""
#         return [
#             ToolSetTestCase(
#                 request="Find events, check if I can afford them, and set reminders",
#                 expected_tools=["find_events", "check_balance", "set_reminder"],
#                 description="Cross-domain planning",
#                 tool_set="multi_domain"
#             ),
#             ToolSetTestCase(
#                 request="Cancel my event and get a refund to my account",
#                 expected_tools=["cancel_event", "check_balance"],
#                 description="Event cancellation with refund check",
#                 tool_set="multi_domain"
#             ),
#             ToolSetTestCase(
#                 request="Track my orders and pay for them",
#                 expected_tools=["track_order", "pay_bill"],
#                 description="Order tracking and payment",
#                 tool_set="multi_domain"
#             )
#         ]


# Create and populate registry
tool_set_registry = ToolSetRegistry()
tool_set_registry.register(TreasureHuntToolSet())
tool_set_registry.register(ProductivityToolSet())
# TODO: Uncomment when tools are updated
# tool_set_registry.register(EventsToolSet())
# tool_set_registry.register(EcommerceToolSet())
# tool_set_registry.register(FinanceToolSet())
# tool_set_registry.register(MultiDomainToolSet())