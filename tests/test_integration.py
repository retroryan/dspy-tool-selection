"""Integration tests for the complete system."""

import pytest
from tool_selection.multi_tool_selector import MultiToolSelector
from tool_selection.registry import registry
from tool_selection.tool_sets import tool_set_registry
from shared_utils.llm_factory import setup_llm


@pytest.fixture(scope="module", autouse=True)
def setup_test_llm():
    """Setup LLM once for all tests."""
    setup_llm()


@pytest.fixture
def treasure_hunt_system():
    """Create a system with treasure hunt tools loaded."""
    # Clear and load only treasure hunt tools
    tool_set_registry.load_tool_set("treasure_hunt")
    
    selector = MultiToolSelector(use_chain_of_thought=True)
    
    return {
        "selector": selector,
        "registry": registry,
        "tools": list(registry.get_all_tools().values())
    }


def test_give_hint(treasure_hunt_system):
    """Test giving a hint about the treasure."""
    decision = treasure_hunt_system["selector"](
        "Give me a hint about the treasure",
        treasure_hunt_system["tools"]
    )
    
    assert len(decision.tool_calls) == 1
    assert decision.tool_calls[0].tool_name == "give_hint"
    
    # Execute the tool
    result = treasure_hunt_system["registry"].execute_tool(
        decision.tool_calls[0].tool_name,
        **decision.tool_calls[0].arguments
    )
    
    assert "hint" in result
    assert isinstance(result["hint"], str)


def test_guess_location(treasure_hunt_system):
    """Test guessing the treasure location."""
    decision = treasure_hunt_system["selector"](
        "I think the treasure is in Seattle",
        treasure_hunt_system["tools"]
    )
    
    assert len(decision.tool_calls) == 1
    assert decision.tool_calls[0].tool_name == "guess_location"
    
    # Execute the tool
    result = treasure_hunt_system["registry"].execute_tool(
        decision.tool_calls[0].tool_name,
        **decision.tool_calls[0].arguments
    )
    
    assert "status" in result
    assert "message" in result


def test_no_tools_needed(treasure_hunt_system):
    """Test request that doesn't need any tools."""
    decision = treasure_hunt_system["selector"](
        "What's the weather like today?",
        treasure_hunt_system["tools"]
    )
    
    # Should return no tools for unrelated request
    assert len(decision.tool_calls) == 0


def test_treasure_hunt_scenarios(treasure_hunt_system):
    """Test various treasure hunt scenarios."""
    scenarios = [
        ("I need help finding the treasure", ["give_hint"]),
        ("Is it at the library?", ["guess_location"]),
        ("Can you give me another clue?", ["give_hint"]),
        ("I think it's in Seattle on Lenora Street", ["guess_location"]),
    ]
    
    for request, expected_tools in scenarios:
        decision = treasure_hunt_system["selector"](
            request,
            treasure_hunt_system["tools"]
        )
        
        # Get selected tool names
        selected_tools = [tc.tool_name for tc in decision.tool_calls]
        
        # Check that expected tools were selected
        for expected in expected_tools:
            assert expected in selected_tools, f"Expected {expected} for request: {request}"


@pytest.mark.parametrize("use_chain_of_thought", [True, False])
def test_selector_modes(use_chain_of_thought):
    """Test both ChainOfThought and Predict modes."""
    # Load treasure hunt tools
    tool_set_registry.load_tool_set("treasure_hunt")
    
    selector = MultiToolSelector(use_chain_of_thought=use_chain_of_thought)
    tools = list(registry.get_all_tools().values())
    
    decision = selector(
        "Give me a hint about the treasure",
        tools
    )
    
    assert len(decision.tool_calls) >= 1
    assert decision.tool_calls[0].tool_name == "give_hint"