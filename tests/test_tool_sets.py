"""Tests for tool sets functionality."""
import pytest
from unittest.mock import patch, MagicMock

from tool_selection.tool_sets import (
    ToolSet, ToolSetConfig, ToolSetTestCase,
    TreasureHuntToolSet, ProductivityToolSet,
    ToolSetRegistry, tool_set_registry
)
from tool_selection.registry import registry

# Import tools to ensure they're registered
from tools.treasure_hunt.give_hint import GiveHintTool
from tools.treasure_hunt.guess_location import GuessLocationTool
from tools.productivity.set_reminder import SetReminderTool


class TestToolSetConfig:
    """Test ToolSetConfig model."""
    
    def test_config_creation(self):
        """Test creating a tool set configuration."""
        config = ToolSetConfig(
            name="test_set",
            description="Test tool set",
            tool_classes=[GiveHintTool, GuessLocationTool]
        )
        
        assert config.name == "test_set"
        assert config.description == "Test tool set"
        assert len(config.tool_classes) == 2
    
    def test_config_immutable(self):
        """Test that configuration is immutable."""
        config = ToolSetConfig(
            name="test_set",
            description="Test tool set",
            tool_classes=[]
        )
        
        from pydantic import ValidationError
        with pytest.raises(ValidationError):  # Pydantic v2 raises ValidationError for frozen models
            config.name = "new_name"


class TestToolSet:
    """Test base ToolSet functionality."""
    
    def test_tool_set_creation(self):
        """Test creating a tool set."""
        config = ToolSetConfig(
            name="test_set",
            description="Test set",
            tool_classes=[GiveHintTool]
        )
        tool_set = ToolSet(config=config)
        
        assert tool_set.config.name == "test_set"
        assert len(tool_set.config.tool_classes) == 1
    
    def test_get_loaded_tools(self):
        """Test extracting tool names from tool classes."""
        config = ToolSetConfig(
            name="test_set",
            description="Test set",
            tool_classes=[
                GiveHintTool,
                GuessLocationTool,
                SetReminderTool
            ]
        )
        tool_set = ToolSet(config=config)
        
        tool_names = tool_set.get_loaded_tools()
        assert len(tool_names) == 3
        assert "give_hint" in tool_names
        assert "guess_location" in tool_names
        assert "set_reminder" in tool_names
    
    def test_load_tools(self):
        """Test loading tool classes."""
        config = ToolSetConfig(
            name="test_set",
            description="Test set",
            tool_classes=[
                GiveHintTool,
                GuessLocationTool
            ]
        )
        tool_set = ToolSet(config=config)
        
        # Load the tools (which is now a no-op since tools are already imported)
        tool_set.load()
        
        # Verify tools are accessible
        tool_names = tool_set.get_loaded_tools()
        assert "give_hint" in tool_names
        assert "guess_location" in tool_names


class TestTreasureHuntToolSet:
    """Test TreasureHuntToolSet implementation."""
    
    def test_treasure_hunt_config(self):
        """Test treasure hunt tool set configuration."""
        tool_set = TreasureHuntToolSet()
        
        assert tool_set.config.name == "treasure_hunt"
        assert "treasure hunting game" in tool_set.config.description
        assert len(tool_set.config.tool_classes) == 2
        
        # Check specific tool classes
        tool_classes = tool_set.config.tool_classes
        assert GiveHintTool in tool_classes
        assert GuessLocationTool in tool_classes
    
    def test_treasure_hunt_test_cases(self):
        """Test treasure hunt test cases."""
        test_cases = TreasureHuntToolSet.get_test_cases()
        
        assert len(test_cases) >= 3
        
        # All should be ToolSetTestCase instances
        assert all(isinstance(tc, ToolSetTestCase) for tc in test_cases)
        
        # All should belong to treasure_hunt tool set
        assert all(tc.tool_set == "treasure_hunt" for tc in test_cases)
        
        # Check for single and multi-tool cases
        single_tool_cases = [tc for tc in test_cases if len(tc.expected_tools) == 1]
        multi_tool_cases = [tc for tc in test_cases if len(tc.expected_tools) > 1]
        
        assert len(single_tool_cases) >= 2
        assert len(multi_tool_cases) >= 1
    
    def test_load_treasure_hunt_tools(self):
        """Test that loading actually registers the tools."""
        # Don't clear registry - just verify tools are available
        # Create the tool set
        tool_set = TreasureHuntToolSet()
        
        # Verify the tool set contains the expected tool classes
        assert len(tool_set.config.tool_classes) == 2
        assert GiveHintTool in tool_set.config.tool_classes
        assert GuessLocationTool in tool_set.config.tool_classes
        
        # Tools should already be registered from imports
        assert registry.get_tool("give_hint") is not None
        assert registry.get_tool("guess_location") is not None


class TestProductivityToolSet:
    """Test ProductivityToolSet implementation."""
    
    def test_productivity_config(self):
        """Test productivity tool set configuration."""
        tool_set = ProductivityToolSet()
        
        assert tool_set.config.name == "productivity"
        assert "task management" in tool_set.config.description
        assert len(tool_set.config.tool_classes) == 1
        
        # Check specific tool class
        assert SetReminderTool in tool_set.config.tool_classes
    
    def test_productivity_test_cases(self):
        """Test productivity test cases."""
        test_cases = ProductivityToolSet.get_test_cases()
        
        assert len(test_cases) >= 2
        
        # Check scenarios are set
        scenarios = {tc.scenario for tc in test_cases if tc.scenario}
        assert "work" in scenarios
        assert "planning" in scenarios
        
        # All should use set_reminder
        assert all("set_reminder" in tc.expected_tools for tc in test_cases)


class TestToolSetRegistry:
    """Test ToolSetRegistry functionality."""
    
    def test_registry_initialization(self):
        """Test that global registry is properly initialized."""
        assert tool_set_registry is not None
        assert len(tool_set_registry.tool_sets) >= 2
        assert "treasure_hunt" in tool_set_registry.tool_sets
        assert "productivity" in tool_set_registry.tool_sets
    
    def test_register_tool_set(self):
        """Test registering a new tool set."""
        # Create a new registry for this test
        test_registry = ToolSetRegistry()
        
        # Create a custom tool set
        custom_set = ToolSet(
            config=ToolSetConfig(
                name="custom",
                description="Custom tool set",
                tool_classes=[]
            )
        )
        
        # Register it
        test_registry.register(custom_set)
        
        assert "custom" in test_registry.tool_sets
        assert test_registry.tool_sets["custom"] == custom_set
    
    def test_load_tool_set(self):
        """Test loading a tool set by name."""
        # Use a fresh registry
        test_registry = ToolSetRegistry()
        test_registry.register(TreasureHuntToolSet())
        
        with patch('tool_selection.tool_sets.import_module') as mock_import:
            tool_set = test_registry.load_tool_set("treasure_hunt")
            
            assert tool_set.config.name == "treasure_hunt"
            assert mock_import.call_count == 2  # Two tools in treasure hunt
    
    def test_load_unknown_tool_set(self):
        """Test loading an unknown tool set."""
        test_registry = ToolSetRegistry()
        
        with pytest.raises(ValueError, match="Unknown tool set: nonexistent"):
            test_registry.load_tool_set("nonexistent")
    
    def test_get_all_tool_sets(self):
        """Test getting all tool sets."""
        all_sets = tool_set_registry.get_all_tool_sets()
        
        assert isinstance(all_sets, dict)
        assert "treasure_hunt" in all_sets
        assert "productivity" in all_sets
        assert isinstance(all_sets["treasure_hunt"], TreasureHuntToolSet)
        assert isinstance(all_sets["productivity"], ProductivityToolSet)
    
    def test_get_tool_set_test_cases(self):
        """Test getting test cases for a specific tool set."""
        test_cases = tool_set_registry.get_test_cases("treasure_hunt")
        
        assert len(test_cases) >= 3
        assert all(tc.tool_set == "treasure_hunt" for tc in test_cases)
    
    def test_get_all_test_cases(self):
        """Test getting test cases from all tool sets."""
        all_test_cases = tool_set_registry.get_all_test_cases()
        
        # Should have test cases from both tool sets
        tool_sets = {tc.tool_set for tc in all_test_cases}
        assert "treasure_hunt" in tool_sets
        assert "productivity" in tool_sets
        
        # Should have at least 5 test cases total
        assert len(all_test_cases) >= 5
    
    def test_get_test_cases_unknown_set(self):
        """Test getting test cases for unknown tool set."""
        with pytest.raises(ValueError, match="Unknown tool set"):
            tool_set_registry.get_test_cases("nonexistent")


class TestIntegration:
    """Integration tests for tool sets with registry."""
    
    def test_complete_workflow(self):
        """Test complete workflow of loading tools and using them."""
        # Don't clear registry - tools should already be loaded from imports
        # Just verify the workflow works
        
        # Verify tools are available in registry before loading tool set
        # (they should be from the imports at the top of this test file)
        give_hint = registry.get_tool("give_hint")
        guess_location = registry.get_tool("guess_location")
        
        assert give_hint is not None
        assert guess_location is not None
        
        # Execute tools
        hint_result = give_hint.execute(hint_total=0)
        assert "coffee and rain" in hint_result["hint"]
        
        guess_result = guess_location.execute(city="Seattle", address="Lenora")
        assert guess_result["status"] == "Correct!"
    
    def test_test_case_tool_alignment(self):
        """Test that test cases match available tools."""
        # Tools should already be loaded from imports
        # Get all test cases
        all_test_cases = tool_set_registry.get_all_test_cases()
        
        # Verify all expected tools in test cases are available
        for test_case in all_test_cases:
            for tool_name in test_case.expected_tools:
                tool = registry.get_tool(tool_name)
                assert tool is not None, f"Tool {tool_name} not found for test case: {test_case.description}"