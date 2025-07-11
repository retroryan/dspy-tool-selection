"""Test for the specific set_reminder issue that was failing."""

import pytest
from tool_selection.multi_tool_selector import MultiToolSelector
from tool_selection.registry import registry
from tools.productivity.set_reminder import SetReminderTool
from tools.treasure_hunt.give_hint import GiveHintTool
from tools.treasure_hunt.guess_location import GuessLocationTool
from shared_utils.llm_factory import setup_llm


@pytest.fixture(scope="module", autouse=True)
def setup_test_llm():
    """Setup LLM once for all tests."""
    setup_llm()


def test_set_reminder_with_meeting_request():
    """Test the specific case that was failing: 'Don't let me forget the meeting at 2pm'."""
    # Clear registry and register only the tool we need
    registry.clear()
    registry.register(SetReminderTool)
    
    selector = MultiToolSelector()
    tools = [SetReminderTool()]
    
    # Test the exact request that was failing
    request = "Don't let me forget the meeting at 2pm"
    decision = selector(request, tools)
    
    # Verify tool selection
    assert len(decision.tool_calls) >= 1
    assert decision.tool_calls[0].tool_name == "set_reminder"
    
    # Verify arguments are correct
    args = decision.tool_calls[0].arguments
    assert "message" in args
    assert "time" in args
    assert args["time"] == "2pm" or "2pm" in args["time"]
    
    # Verify execution works
    result = registry.execute_tool("set_reminder", **args)
    assert result["status"] == "success"
    assert "Reminder set" in result["message"]


def test_various_reminder_phrasings():
    """Test different ways of requesting reminders."""
    # Clear registry and register only the tool we need
    registry.clear()
    registry.register(SetReminderTool)
    
    selector = MultiToolSelector()
    tools = [SetReminderTool()]
    
    test_cases = [
        "Remind me to call mom at 3pm",
        "Set a reminder for tomorrow to buy groceries", 
        "I need a reminder in 30 minutes to check the oven",
        "Don't let me forget the meeting at 2pm",
        "Please remind me about the dentist appointment at 10am"
    ]
    
    for request in test_cases:
        decision = selector(request, tools)
        
        # Should select set_reminder
        assert len(decision.tool_calls) >= 1
        assert decision.tool_calls[0].tool_name == "set_reminder"
        
        # Should have both required arguments
        args = decision.tool_calls[0].arguments
        assert "message" in args, f"Missing 'message' for request: {request}"
        assert "time" in args, f"Missing 'time' for request: {request}"
        
        # Should execute successfully
        result = registry.execute_tool("set_reminder", **args)
        assert result["status"] == "success"