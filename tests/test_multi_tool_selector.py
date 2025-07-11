"""
This module contains unit tests for the MultiToolSelector, which is responsible for
selecting appropriate tools based on a user's request using DSPy.

It defines mock tool classes and uses pytest fixtures to set up the testing environment.
"""

import pytest
from tool_selection.multi_tool_selector import MultiToolSelector
from tool_selection.models import MultiToolDecision, ToolCall
from tool_selection.base_tool import BaseTool, ToolArgument
from shared_utils.llm_factory import setup_llm
from typing import ClassVar, Dict, Any, Type
from pydantic import BaseModel, Field


@pytest.fixture(scope="module", autouse=True)
def setup_test_llm():
    """
    Fixture to set up the Language Model (LLM) for all tests in this module.
    This ensures the DSPy components can interact with a configured LLM.
    """
    setup_llm()


# --- Mock Tool Definitions for Testing ---
# These classes simulate real tools and are used to test the MultiToolSelector's
# ability to correctly identify and extract arguments for various tool types.

class FindEventsTool(BaseTool):
    """A mock tool for finding events."""
    NAME: ClassVar[str] = "find_events"
    MODULE: ClassVar[str] = "tests.test_multi_tool_selector"
    
    class Arguments(BaseModel):
        event_type: str = Field(..., description="Type of event")
        location: str = Field(..., description="Location")
    
    description: str = "Find events in a location"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, event_type: str, location: str) -> Dict[str, Any]:
        return {"events": [f"{event_type} in {location}"]}


class CheckBalanceTool(BaseTool):
    """A mock tool for checking account balances."""
    NAME: ClassVar[str] = "check_balance"
    MODULE: ClassVar[str] = "tests.test_multi_tool_selector"
    
    class Arguments(BaseModel):
        account_type: str = Field(default="checking", description="Account type")
    
    description: str = "Check account balance"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, account_type: str = "checking") -> Dict[str, Any]:
        return {"balance": "$1000"}


class SearchProductsTool(BaseTool):
    """A mock tool for searching products."""
    NAME: ClassVar[str] = "search_products"
    MODULE: ClassVar[str] = "tests.test_multi_tool_selector"
    
    class Arguments(BaseModel):
        query: str = Field(..., description="Search query")
        category: str = Field(default="all", description="Product category")
    
    description: str = "Search for products"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, query: str, category: str = "all") -> Dict[str, Any]:
        return {"products": [f"{query} in {category}"]}


@pytest.fixture
def sample_tools():
    """
    Provides a list of instantiated mock tools for tests to use.
    This simulates the available tools the MultiToolSelector would choose from.
    """
    return [
        FindEventsTool(),
        CheckBalanceTool(),
        SearchProductsTool()
    ]


@pytest.fixture
def selector():
    """
    Provides an instance of MultiToolSelector configured to use Chain-of-Thought.
    This is the primary component under test.
    """
    return MultiToolSelector(use_chain_of_thought=True)


# --- Test Cases for MultiToolSelector Functionality ---

def test_single_tool_selection(selector, sample_tools):
    """
    Tests that the selector can correctly identify and select a single tool
    and extract its arguments from a user request.
    """
    decision = selector("Check my savings account balance", sample_tools)
    
    assert isinstance(decision, MultiToolDecision)
    assert len(decision.tool_calls) == 1
    assert decision.tool_calls[0].tool_name == "check_balance"
    assert "account_type" in decision.tool_calls[0].arguments


def test_multi_tool_selection(selector, sample_tools):
    """
    Tests the selector's ability to identify and select multiple tools
    required to fulfill a complex user request.
    """
    decision = selector(
        "Find concerts in Seattle and check if I have enough money",
        sample_tools
    )
    
    assert isinstance(decision, MultiToolDecision)
    assert len(decision.tool_calls) == 2
    
    tool_names = [tc.tool_name for tc in decision.tool_calls]
    assert "find_events" in tool_names
    assert "check_balance" in tool_names


def test_tool_call_structure(selector, sample_tools):
    """
    Verifies that the output of the selector (ToolCall objects) adheres
    to the expected data structure, including tool name and arguments.
    """
    decision = selector("Search for laptops", sample_tools)
    
    assert len(decision.tool_calls) >= 1
    
    for tool_call in decision.tool_calls:
        assert isinstance(tool_call, ToolCall)
        assert isinstance(tool_call.tool_name, str)
        assert isinstance(tool_call.arguments, dict)


def test_predict_mode():
    """
    Tests the MultiToolSelector when configured to use `dspy.Predict`
    instead of `dspy.ChainOfThought`, ensuring basic functionality.
    """
    selector_predict = MultiToolSelector(use_chain_of_thought=False)
    
    tools = [CheckBalanceTool()]
    
    decision = selector_predict("Check my balance", tools)
    
    assert isinstance(decision, MultiToolDecision)
    assert len(decision.tool_calls) >= 1


def test_multi_tool_request(selector, sample_tools):
    """
    Tests a more complex multi-tool request, ensuring the selector can
    handle multiple tools and correctly extract their respective arguments.
    """
    decision = selector(
        "Find electronics stores in downtown, search for gaming laptops under $1000",
        sample_tools
    )
    
    assert isinstance(decision, MultiToolDecision)
    assert len(decision.tool_calls) >= 1
    
    # Should use search_products
    product_searches = [tc for tc in decision.tool_calls if tc.tool_name == "search_products"]
    assert len(product_searches) >= 1
    
    # Check arguments are extracted
    for ps in product_searches:
        assert ps.arguments  # Should have arguments


