"""
Test explicit tool registration without decorators.

This test validates the new explicit registration pattern using
ToolSetRegistry and the factory functions.
"""

import pytest
from typing import Dict, Any
from pydantic import BaseModel, Field

from shared.tool_set_registry import (
    ToolSetRegistry, 
    create_tool_set_registry,
    create_ecommerce_tool_set_registry,
    create_productivity_tool_set_registry
)
from shared.models import ToolCall, ToolExecutionResult
from agentic_loop.activity_manager import ActivityManager
from agentic_loop.manual_agent_loop import ManualAgentLoop
from tool_selection.base_tool import BaseTool, ToolArgument


class TestExplicitRegistration:
    """Test the new explicit registration pattern."""
    
    def test_tool_set_registry_creation(self):
        """Test creating a tool set registry."""
        registry = ToolSetRegistry()
        assert isinstance(registry, ToolSetRegistry)
        assert registry.get_tool_names() == []
        assert registry.get_loaded_tool_sets() == {}
    
    def test_explicit_tool_registration(self):
        """Test registering tools explicitly."""
        registry = ToolSetRegistry()
        
        # Create a mock tool class
        class MockTool(BaseTool):
            NAME = "mock_tool"
            MODULE = "test"
            
            def __init__(self):
                super().__init__(
                    description="A mock tool",
                    arguments=[
                        ToolArgument(
                            name="input",
                            type="str",
                            description="Input value",
                            required=True
                        )
                    ]
                )
            
            def execute(self, **kwargs) -> Dict[str, Any]:
                return {"result": f"Mock: {kwargs.get('input', 'default')}"}
        
        # Register the tool set
        registry.register_tool_set(
            tool_set_name="test_set",
            description="Test tool set",
            tool_classes=[MockTool]
        )
        
        # Verify registration
        assert "mock_tool" in registry.get_tool_names()
        assert "test_set" in registry.get_loaded_tool_sets()
        assert registry.get_loaded_tool_sets()["test_set"] == "Test tool set"
    
    def test_tool_execution_through_registry(self):
        """Test executing tools through the registry."""
        registry = ToolSetRegistry()
        
        # Create a mock tool class
        class TestTool(BaseTool):
            NAME = "test_tool"
            MODULE = "test"
            
            def __init__(self):
                super().__init__(
                    description="A test tool",
                    arguments=[
                        ToolArgument(
                            name="message",
                            type="str",
                            description="Message to process",
                            required=True
                        )
                    ]
                )
            
            def execute(self, **kwargs) -> Dict[str, Any]:
                return {"processed": kwargs.get('message', 'no message')}
        
        # Register the tool set
        registry.register_tool_set(
            tool_set_name="test",
            description="Test tools",
            tool_classes=[TestTool]
        )
        
        # Execute a tool
        tool_call = ToolCall(
            tool_name="test_tool",
            arguments={"message": "hello world"}
        )
        
        result = registry.execute_tool(tool_call)
        
        # Verify execution
        assert isinstance(result, ToolExecutionResult)
        assert result.success is True
        assert result.result == {"processed": "hello world"}
        assert result.tool_name == "test_tool"
    
    def test_factory_function_treasure_hunt(self):
        """Test the treasure hunt factory function."""
        registry = create_tool_set_registry()
        
        # Should have treasure hunt tools loaded
        tool_names = registry.get_tool_names()
        assert "give_hint" in tool_names
        assert "guess_location" in tool_names
        
        # Should have treasure hunt tool set loaded
        loaded_sets = registry.get_loaded_tool_sets()
        assert "treasure_hunt" in loaded_sets
        assert "treasure hunting" in loaded_sets["treasure_hunt"].lower()
    
    def test_factory_function_ecommerce(self):
        """Test the ecommerce factory function."""
        registry = create_ecommerce_tool_set_registry()
        
        # Should have ecommerce tools loaded
        tool_names = registry.get_tool_names()
        expected_tools = [
            "get_order", "list_orders", "add_to_cart", 
            "search_products", "track_order", "return_item"
        ]
        
        for tool in expected_tools:
            assert tool in tool_names
        
        # Should have ecommerce tool set loaded
        loaded_sets = registry.get_loaded_tool_sets()
        assert "ecommerce" in loaded_sets
        assert "commerce" in loaded_sets["ecommerce"].lower()
    
    def test_factory_function_productivity(self):
        """Test the productivity factory function."""
        registry = create_productivity_tool_set_registry()
        
        # Should have productivity tools loaded
        tool_names = registry.get_tool_names()
        assert "set_reminder" in tool_names
        
        # Should have productivity tool set loaded
        loaded_sets = registry.get_loaded_tool_sets()
        assert "productivity" in loaded_sets
        assert "productivity" in loaded_sets["productivity"].lower()
    
    def test_activity_manager_with_explicit_registry(self):
        """Test ActivityManager with explicit tool set registry."""
        # Create registry with specific tools
        registry = create_tool_set_registry()
        
        # Create a simple mock agent loop
        class MockAgentLoop:
            def __init__(self):
                pass
            
            def get_next_action(self, conversation_state):
                from shared.models import ActionDecision, ActionType
                
                return ActionDecision(
                    action_type=ActionType.FINAL_RESPONSE,
                    reasoning="Task complete",
                    tool_calls=[],
                    final_response="Explicit registration test completed",
                    should_continue=False
                )
        
        # Create activity manager
        agent_loop = MockAgentLoop()
        activity_manager = ActivityManager(
            agent_loop=agent_loop,
            tool_registry=registry,
            max_iterations=3,
            timeout_seconds=10.0
        )
        
        # Test getting available tools
        tools = activity_manager.get_available_tools()
        assert "give_hint" in tools
        assert "guess_location" in tools
        
        # Test running activity
        result = activity_manager.run_activity(
            user_query="Test explicit registration",
            goal="Test the new pattern"
        )
        
        # Verify
        assert result.status == "completed"
        assert result.final_response == "Explicit registration test completed"
        assert result.tool_set_name == "unknown"  # No tool set name set in conversation state
    
    def test_registry_isolation(self):
        """Test that different registries are isolated."""
        # Create two different registries
        registry1 = create_tool_set_registry()  # treasure hunt
        registry2 = create_ecommerce_tool_set_registry()  # ecommerce
        
        # They should have different tools
        tools1 = registry1.get_tool_names()
        tools2 = registry2.get_tool_names()
        
        # No overlap expected
        assert "give_hint" in tools1
        assert "give_hint" not in tools2
        assert "get_order" in tools2
        assert "get_order" not in tools1
        
        # Different tool sets
        sets1 = registry1.get_loaded_tool_sets()
        sets2 = registry2.get_loaded_tool_sets()
        
        assert "treasure_hunt" in sets1
        assert "treasure_hunt" not in sets2
        assert "ecommerce" in sets2
        assert "ecommerce" not in sets1
    
    def test_registry_clear_and_reload(self):
        """Test clearing and reloading registry."""
        registry = create_tool_set_registry()
        
        # Should have tools initially
        assert len(registry.get_tool_names()) > 0
        assert len(registry.get_loaded_tool_sets()) > 0
        
        # Clear registry
        registry.clear()
        
        # Should be empty
        assert len(registry.get_tool_names()) == 0
        assert len(registry.get_loaded_tool_sets()) == 0
        
        # Reload with different tool set
        from tool_selection.tool_sets import ProductivityToolSet
        productivity = ProductivityToolSet()
        
        registry.register_tool_set(
            tool_set_name="productivity",
            description=productivity.config.description,
            tool_classes=productivity.config.tool_classes
        )
        
        # Should have new tools
        assert "set_reminder" in registry.get_tool_names()
        assert "productivity" in registry.get_loaded_tool_sets()
    
    def test_real_tool_execution(self):
        """Test executing actual tools from the system."""
        registry = create_tool_set_registry()
        
        # Test give_hint tool
        hint_call = ToolCall(
            tool_name="give_hint",
            arguments={}
        )
        
        result = registry.execute_tool(hint_call)
        assert result.success is True
        assert "hint" in str(result.result).lower()
        
        # Test guess_location tool
        guess_call = ToolCall(
            tool_name="guess_location",
            arguments={"location": "library"}
        )
        
        result = registry.execute_tool(guess_call)
        assert result.success is True
        # The result should contain feedback about the guess
        assert result.result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])