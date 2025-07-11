"""Integration tests for the complete system."""

import pytest
from tool_selection.multi_tool_selector import MultiToolSelector
from tool_selection.tool_registry import MultiToolRegistry
from shared_utils.llm_factory import setup_llm


@pytest.fixture(scope="module", autouse=True)
def setup_test_llm():
    """Setup LLM once for all tests."""
    setup_llm()


@pytest.fixture
def system():
    """Create a complete system with selector and registry."""
    registry = MultiToolRegistry()
    registry.register_all_tools()
    selector = MultiToolSelector(use_predict=False)
    
    return {
        "selector": selector,
        "registry": registry,
        "tools": registry.get_tool_definitions()
    }


def test_end_to_end_single_tool(system):
    """Test complete flow with a single tool."""
    # Select tool
    decision = system["selector"](
        "Check my savings account balance",
        system["tools"]
    )
    
    # Execute tool
    results = system["registry"].execute(decision)
    
    assert len(results) == 1
    assert results[0]["tool"] == "check_balance"
    assert "result" in results[0] or "error" in results[0]


def test_end_to_end_multi_tool(system):
    """Test complete flow with multiple tools."""
    # Select tools
    decision = system["selector"](
        "Find concerts in Seattle and check ticket prices",
        system["tools"]
    )
    
    # Execute tools
    results = system["registry"].execute(decision)
    
    assert len(results) >= 1
    for result in results:
        assert "tool" in result
        assert "result" in result or "error" in result


def test_multi_tool_scenarios(system):
    """Test various multi-tool scenarios from the demo."""
    test_cases = [
        {
            "request": "Transfer $500 from savings to checking",
            "expected_tools": ["transfer_money"]
        },
        {
            "request": "Find electronics under $1000",
            "expected_tools": ["search_products"]
        },
        {
            "request": "Cancel my event EVT123 due to schedule conflict",
            "expected_tools": ["cancel_event"]
        }
    ]
    
    for test in test_cases:
        decision = system["selector"](test["request"], system["tools"])
        
        # Check that the selector returned at least one tool
        assert len(decision.tool_calls) >= 1, f"No tools selected for request: {test['request']}. Reasoning: {decision.reasoning}"
        
        results = system["registry"].execute(decision)
        
        assert len(results) >= 1
        
        # Check that at least one expected tool was selected
        selected_tools = [tc.tool_name for tc in decision.tool_calls]
        matching_tools = [t for t in test["expected_tools"] if t in selected_tools]
        assert len(matching_tools) >= 1, f"Expected one of {test['expected_tools']}, got {selected_tools}"


def test_error_handling(system):
    """Test system behavior with edge cases."""
    # Empty request
    decision = system["selector"]("", system["tools"])
    assert len(decision.tool_calls) >= 0  # Should handle gracefully
    
    # Very long request
    long_request = "I need to " + " and ".join([
        "find events", "check balance", "transfer money", 
        "search products", "track orders"
    ] * 5)
    
    decision = system["selector"](long_request, system["tools"])
    results = system["registry"].execute(decision)
    
    # Should still work but might limit number of tools
    assert isinstance(results, list)


@pytest.mark.parametrize("use_predict", [False, True])
def test_both_modes(use_predict):
    """Test both ChainOfThought and Predict modes."""
    registry = MultiToolRegistry()
    registry.register_all_tools()
    selector = MultiToolSelector(use_predict=use_predict)
    
    decision = selector(
        "Check my balance",
        registry.get_tool_definitions()
    )
    
    assert len(decision.tool_calls) >= 1
    assert decision.tool_calls[0].tool_name == "check_balance"