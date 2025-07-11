"""Test that tool arguments are properly extracted from args_model."""

import pytest
from tool_selection.base_tool import BaseTool, ToolArgument
from tool_selection.registry import registry
from tools.productivity.set_reminder import SetReminderTool
from tools.treasure_hunt.give_hint import GiveHintTool
from tools.treasure_hunt.guess_location import GuessLocationTool


def test_set_reminder_arguments():
    """Test that SetReminderTool has correct arguments from its args_model."""
    tool = SetReminderTool()
    
    # Check that arguments are populated
    assert len(tool.arguments) == 2
    
    # Check argument names
    arg_names = {arg.name for arg in tool.arguments}
    assert arg_names == {"message", "time"}
    
    # Check specific argument details
    message_arg = next(arg for arg in tool.arguments if arg.name == "message")
    assert message_arg.type == "string"
    assert message_arg.required is True
    assert "reminder message" in message_arg.description
    
    time_arg = next(arg for arg in tool.arguments if arg.name == "time")
    assert time_arg.type == "string"
    assert time_arg.required is True
    assert "2pm" in time_arg.description  # Check that examples are in description


def test_give_hint_arguments():
    """Test that GiveHintTool has correct arguments from its args_model."""
    tool = GiveHintTool()
    
    # Check that arguments are populated
    assert len(tool.arguments) == 1
    
    # Check argument details
    hint_arg = tool.arguments[0]
    assert hint_arg.name == "hint_total"
    assert hint_arg.type == "integer"
    assert hint_arg.required is False  # Has default value
    assert hint_arg.default == 0
    assert "hints already given" in hint_arg.description


def test_guess_location_arguments():
    """Test that GuessLocationTool has correct arguments from its args_model."""
    tool = GuessLocationTool()
    
    # Check that arguments are populated
    assert len(tool.arguments) == 3
    
    # Check argument names and requirements
    arg_dict = {arg.name: arg for arg in tool.arguments}
    assert set(arg_dict.keys()) == {"address", "city", "state"}
    
    # All arguments should have defaults (empty strings)
    for arg in tool.arguments:
        assert arg.default == ""
        assert arg.type == "string"


def test_tool_selector_sees_arguments():
    """Test that the MultiToolSelector can see tool arguments."""
    from tool_selection.multi_tool_selector import MultiToolSelector, ToolInfo
    
    # Create tool and convert to ToolInfo
    tool = SetReminderTool()
    tool_info = ToolInfo(
        name=tool.name,
        description=tool.description,
        arguments=tool.arguments
    )
    
    # Verify the tool info has the arguments
    assert len(tool_info.arguments) == 2
    assert all(isinstance(arg, ToolArgument) for arg in tool_info.arguments)


def test_argument_validation_with_execute():
    """Test that tool execution validates arguments properly."""
    tool = SetReminderTool()
    
    # Test with valid arguments
    result = tool.validate_and_execute(message="Meeting", time="2pm")
    assert result["status"] == "success"
    assert "Meeting" in result["message"]
    assert "2pm" in result["message"]
    
    # Test with missing required argument
    with pytest.raises(Exception) as exc_info:
        tool.validate_and_execute(time="2pm")  # Missing message
    assert "message" in str(exc_info.value).lower()


def test_registry_tools_have_arguments():
    """Test that tools in the registry have their arguments populated."""
    # Import tools to ensure they're registered
    from tools.productivity.set_reminder import SetReminderTool
    from tools.treasure_hunt.give_hint import GiveHintTool
    from tools.treasure_hunt.guess_location import GuessLocationTool
    
    # Check each tool in the registry
    all_tools = registry.get_all_tools()
    
    for tool_name, tool in all_tools.items():
        if tool.args_model:
            # If tool has an args_model, it should have arguments
            assert len(tool.arguments) > 0, f"{tool_name} has args_model but no arguments"
            
            # Each argument should have required fields
            for arg in tool.arguments:
                assert arg.name
                assert arg.type
                assert arg.description