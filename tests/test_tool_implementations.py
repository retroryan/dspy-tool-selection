"""Tests for actual tool implementations."""
import pytest
from pydantic import ValidationError

# Import tools to register them
from tools.treasure_hunt.give_hint import GiveHintTool
from tools.treasure_hunt.guess_location import GuessLocationTool
from tools.productivity.set_reminder import SetReminderTool
from tool_selection.registry import registry


class TestGiveHintTool:
    """Test cases for GiveHintTool."""
    
    def test_tool_registration(self):
        """Test that tool is properly registered."""
        tool = registry.get_tool("give_hint")
        assert tool is not None
        assert isinstance(tool, GiveHintTool)
        assert tool.metadata.name == "give_hint"
        assert tool.metadata.category == "treasure_hunt"
    
    def test_give_first_hint(self):
        """Test giving the first hint."""
        tool = registry.get_tool("give_hint")
        result = tool.execute(hint_total=0)
        assert "hint" in result
        assert "coffee and rain" in result["hint"]
    
    def test_give_second_hint(self):
        """Test giving the second hint."""
        tool = registry.get_tool("give_hint")
        result = tool.execute(hint_total=1)
        assert "hint" in result
        assert "public market" in result["hint"]
    
    def test_give_third_hint(self):
        """Test giving the third hint."""
        tool = registry.get_tool("give_hint")
        result = tool.execute(hint_total=2)
        assert "hint" in result
        assert "President's wife" in result["hint"]
    
    def test_no_more_hints(self):
        """Test when all hints are exhausted."""
        tool = registry.get_tool("give_hint")
        result = tool.execute(hint_total=3)
        assert "hint" in result
        assert "No more hints available" in result["hint"]
    
    def test_default_hint_total(self):
        """Test default value for hint_total."""
        tool = registry.get_tool("give_hint")
        result = tool.execute()
        assert "hint" in result
        assert "coffee and rain" in result["hint"]
    
    def test_validation_with_registry(self):
        """Test validation through registry execute_tool."""
        # Valid execution
        result = registry.execute_tool("give_hint", hint_total=1)
        assert "public market" in result["hint"]
        
        # Invalid type should raise error
        with pytest.raises(ValidationError):
            registry.execute_tool("give_hint", hint_total="not a number")
        
        # Negative number should raise error
        with pytest.raises(ValidationError):
            registry.execute_tool("give_hint", hint_total=-1)
    
    def test_args_model_validation(self):
        """Test the GiveHintTool.Arguments model directly."""
        # Valid args
        args = GiveHintTool.Arguments(hint_total=2)
        assert args.hint_total == 2
        
        # Default value
        args = GiveHintTool.Arguments()
        assert args.hint_total == 0
        
        # Invalid negative value
        with pytest.raises(ValidationError):
            GiveHintTool.Arguments(hint_total=-5)
    
    def test_tool_test_cases(self):
        """Test that tool defines appropriate test cases."""
        test_cases = GiveHintTool.get_test_cases()
        assert len(test_cases) >= 3
        assert all(tc.expected_tools == ["give_hint"] for tc in test_cases)


class TestGuessLocationTool:
    """Test cases for GuessLocationTool."""
    
    def test_tool_registration(self):
        """Test that tool is properly registered."""
        tool = registry.get_tool("guess_location")
        assert tool is not None
        assert isinstance(tool, GuessLocationTool)
        assert tool.metadata.name == "guess_location"
        assert tool.metadata.category == "treasure_hunt"
    
    def test_correct_guess(self):
        """Test a correct location guess."""
        tool = registry.get_tool("guess_location")
        result = tool.execute(address="123 Lenora St", city="Seattle", state="WA")
        assert result["status"] == "Correct!"
        assert "found the treasure" in result["message"]
    
    def test_incorrect_guess(self):
        """Test an incorrect location guess."""
        tool = registry.get_tool("guess_location")
        result = tool.execute(address="456 Main St", city="Portland", state="OR")
        assert result["status"] == "Incorrect"
        assert "not the right location" in result["message"]
    
    def test_partial_correct_city(self):
        """Test with only correct city."""
        tool = registry.get_tool("guess_location")
        result = tool.execute(city="Seattle")
        assert result["status"] == "Incorrect"  # Need both city and address
    
    def test_partial_correct_address(self):
        """Test with only correct address."""
        tool = registry.get_tool("guess_location")
        result = tool.execute(address="Lenora Street")
        assert result["status"] == "Incorrect"  # Need both city and address
    
    def test_case_insensitive(self):
        """Test that matching is case insensitive."""
        tool = registry.get_tool("guess_location")
        result = tool.execute(address="LENORA AVE", city="SEATTLE")
        assert result["status"] == "Correct!"
    
    def test_default_values(self):
        """Test with all default values."""
        tool = registry.get_tool("guess_location")
        result = tool.execute()
        assert result["status"] == "Incorrect"
    
    def test_validation_with_registry(self):
        """Test validation through registry."""
        # Valid execution with all fields
        result = registry.execute_tool(
            "guess_location",
            address="test",
            city="test",
            state="test"
        )
        assert "status" in result
        
        # Valid execution with partial fields
        result = registry.execute_tool("guess_location", city="Seattle")
        assert "status" in result
    
    def test_args_model_validation(self):
        """Test the GuessLocationTool.Arguments model directly."""
        # All fields provided
        args = GuessLocationTool.Arguments(address="123 Main", city="Seattle", state="WA")
        assert args.address == "123 Main"
        assert args.city == "Seattle"
        assert args.state == "WA"
        
        # No fields provided - should set defaults
        args = GuessLocationTool.Arguments()
        assert args.address == ""
        assert args.city == ""
        assert args.state == ""


class TestSetReminderTool:
    """Test cases for SetReminderTool."""
    
    def test_tool_registration(self):
        """Test that tool is properly registered."""
        tool = registry.get_tool("set_reminder")
        assert tool is not None
        assert isinstance(tool, SetReminderTool)
        assert tool.metadata.name == "set_reminder"
        assert tool.metadata.category == "productivity"
    
    def test_set_reminder_success(self):
        """Test successful reminder creation."""
        tool = registry.get_tool("set_reminder")
        result = tool.execute(message="Call mom", time="3pm")
        
        assert result["status"] == "success"
        assert "Call mom" in result["message"]
        assert "3pm" in result["message"]
        assert "reminder_id" in result
        assert result["reminder_id"].startswith("rem_")
    
    def test_long_message(self):
        """Test with a long message."""
        tool = registry.get_tool("set_reminder")
        long_message = "Remember to " + "do something " * 20
        result = tool.execute(message=long_message, time="tomorrow")
        
        assert result["status"] == "success"
        assert long_message in result["message"]
    
    def test_various_time_formats(self):
        """Test with various time formats."""
        tool = registry.get_tool("set_reminder")
        time_formats = ["2pm", "tomorrow", "in 30 minutes", "next Monday", "5:30 PM"]
        
        for time_format in time_formats:
            result = tool.execute(message="Test", time=time_format)
            assert result["status"] == "success"
            assert time_format in result["message"]
    
    def test_validation_with_registry(self):
        """Test validation through registry."""
        # Valid execution
        result = registry.execute_tool(
            "set_reminder",
            message="Test reminder",
            time="2pm"
        )
        assert result["status"] == "success"
        
        # Missing required field
        with pytest.raises(ValidationError):
            registry.execute_tool("set_reminder", message="Test")
        
        # Empty message
        with pytest.raises(ValidationError):
            registry.execute_tool("set_reminder", message="", time="2pm")
        
        # Message too long
        with pytest.raises(ValidationError):
            registry.execute_tool(
                "set_reminder",
                message="x" * 501,
                time="2pm"
            )
    
    def test_args_model_validation(self):
        """Test the SetReminderTool.Arguments model directly."""
        # Valid args
        args = SetReminderTool.Arguments(message="Call dentist", time="tomorrow at 9am")
        assert args.message == "Call dentist"
        assert args.time == "tomorrow at 9am"
        
        # Empty message should fail
        with pytest.raises(ValidationError):
            SetReminderTool.Arguments(message="", time="2pm")
        
        # Empty time should fail
        with pytest.raises(ValidationError):
            SetReminderTool.Arguments(message="Test", time="")
        
        # Message too long
        with pytest.raises(ValidationError):
            SetReminderTool.Arguments(message="x" * 501, time="2pm")
    
    def test_tool_test_cases(self):
        """Test that tool defines appropriate test cases."""
        test_cases = SetReminderTool.get_test_cases()
        assert len(test_cases) >= 4
        assert all(tc.expected_tools == ["set_reminder"] for tc in test_cases)


class TestToolCategories:
    """Test tool categorization."""
    
    def test_category_filtering(self):
        """Test filtering tools by category."""
        # Get treasure hunt tools
        treasure_tools = registry.get_tools_by_category("treasure_hunt")
        assert len(treasure_tools) == 2
        assert "give_hint" in treasure_tools
        assert "guess_location" in treasure_tools
        assert "set_reminder" not in treasure_tools
        
        # Get productivity tools
        productivity_tools = registry.get_tools_by_category("productivity")
        assert len(productivity_tools) == 1
        assert "set_reminder" in productivity_tools
        assert "give_hint" not in productivity_tools
    
    def test_all_tools_registered(self):
        """Test that all expected tools are registered."""
        all_tools = registry.get_all_tools()
        expected_tools = {"give_hint", "guess_location", "set_reminder"}
        
        # Check all expected tools are present
        for tool_name in expected_tools:
            assert tool_name in all_tools
    
    def test_aggregated_test_cases(self):
        """Test getting test cases from all tools."""
        all_test_cases = registry.get_all_test_cases()
        
        # Should have test cases from all three tools
        tool_names = set()
        for tc in all_test_cases:
            tool_names.update(tc.expected_tools)
        
        assert "give_hint" in tool_names
        assert "guess_location" in tool_names
        assert "set_reminder" in tool_names
        
        # Should have at least 10 test cases total
        assert len(all_test_cases) >= 10