"""Tests for the multi-tool selector."""

import pytest
from tool_selection.multi_tool_selector import MultiToolSelector, MultiToolDecision, ToolCall
from tool_selection.models import MultiTool, MultiToolName, MultiToolDecision, ToolArgument
from shared_utils.llm_factory import setup_llm


@pytest.fixture(scope="module", autouse=True)
def setup_test_llm():
    """Setup LLM once for all tests."""
    setup_llm()


@pytest.fixture
def sample_tools():
    """Create sample tools for testing."""
    return [
        MultiTool(
            name=MultiToolName.FIND_EVENTS,
            description="Find events in a location",
            category="events",
            arguments=[
                ToolArgument(name="event_type", type="str", description="Type of event"),
                ToolArgument(name="location", type="str", description="Location")
            ]
        ),
        MultiTool(
            name=MultiToolName.CHECK_BALANCE,
            description="Check account balance",
            category="finance",
            arguments=[
                ToolArgument(name="account_type", type="str", description="Account type")
            ]
        ),
        MultiTool(
            name=MultiToolName.SEARCH_PRODUCTS,
            description="Search for products",
            category="shopping",
            arguments=[
                ToolArgument(name="query", type="str", description="Search query"),
                ToolArgument(name="category", type="str", description="Product category")
            ]
        )
    ]


@pytest.fixture
def selector():
    """Create a multi-tool selector instance."""
    return MultiToolSelector(use_predict=False)


def test_single_tool_selection(selector, sample_tools):
    """Test selecting a single tool."""
    decision = selector("Check my savings account balance", sample_tools)
    
    assert isinstance(decision, MultiToolDecision)
    assert len(decision.tool_calls) == 1
    assert decision.tool_calls[0].tool_name == "check_balance"
    assert "account_type" in decision.tool_calls[0].arguments


def test_multi_tool_selection(selector, sample_tools):
    """Test selecting multiple tools."""
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
    """Test that tool calls have the correct structure."""
    decision = selector("Search for laptops", sample_tools)
    
    assert len(decision.tool_calls) >= 1
    
    for tool_call in decision.tool_calls:
        assert isinstance(tool_call, ToolCall)
        assert isinstance(tool_call.tool_name, str)
        assert isinstance(tool_call.arguments, dict)


def test_predict_mode():
    """Test using Predict mode for faster inference."""
    selector_predict = MultiToolSelector(use_predict=True)
    
    tools = [
        MultiTool(
            name=MultiToolName.CHECK_BALANCE,
            description="Check balance",
            category="finance",
            arguments=[]
        )
    ]
    
    decision = selector_predict("Check my balance", tools)
    
    assert isinstance(decision, MultiToolDecision)
    assert len(decision.tool_calls) >= 1


def test_multi_tool_request(selector, sample_tools):
    """Test a multi-tool request requiring multiple tools with arguments."""
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


def test_empty_tools_list(selector):
    """Test behavior with no available tools."""
    with pytest.raises(Exception):  # Should raise when no tools available
        selector("Do something", [])