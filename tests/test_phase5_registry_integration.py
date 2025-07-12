"""
Test Phase 5: Tool Registry Integration with ActivityManager

This test verifies that the new shared/registry.py works correctly
with the ActivityManager for tool execution.
"""

import pytest
from typing import Dict, Any
from pydantic import BaseModel, Field

from shared.tool_set_registry import ToolSetRegistry
from shared.models import ToolCall, ToolExecutionResult, ConversationState
from agentic_loop.activity_manager import ActivityManager
from agentic_loop.manual_agent_loop import ManualAgentLoop
from agentic_loop.agent_reasoner import AgentReasoner
from tool_selection.base_tool import BaseTool, ToolArgument


class MockToolArgs(BaseModel):
    """Arguments for mock tool."""
    message: str = Field(..., description="Test message")


class MockTool(BaseTool):
    """Mock tool for testing registry integration."""
    
    NAME = "mock_tool"
    MODULE = "test"
    
    def __init__(self):
        super().__init__(
            description="A mock tool for testing",
            arguments=[
                ToolArgument(
                    name="message",
                    type="str",
                    description="Test message",
                    required=True
                )
            ],
            args_model=MockToolArgs
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Mock execution."""
        return {"result": f"Mock response: {kwargs.get('message', 'default')}"}


class FailingMockTool(BaseTool):
    """Mock tool that always fails for testing error handling."""
    
    NAME = "failing_tool"
    MODULE = "test"
    
    def __init__(self):
        super().__init__(
            description="A mock tool that always fails",
            arguments=[
                ToolArgument(
                    name="input",
                    type="str",
                    description="Input that doesn't matter",
                    required=True
                )
            ]
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Always fails."""
        raise Exception("This tool always fails")


class TestRegistryIntegration:
    """Test the registry integration with ActivityManager."""
    
    def test_registry_execute_tool_success(self):
        """Test successful tool execution through registry."""
        # Setup
        registry = ToolSetRegistry()
        registry.register_tool_set(
            tool_set_name="test",
            description="Test tools",
            tool_classes=[MockTool]
        )
        
        # Create tool call
        tool_call = ToolCall(
            tool_name="mock_tool",
            arguments={"message": "hello world"}
        )
        
        # Execute
        result = registry.execute_tool(tool_call)
        
        # Verify
        assert isinstance(result, ToolExecutionResult)
        assert result.tool_name == "mock_tool"
        assert result.success is True
        assert result.result == {"result": "Mock response: hello world"}
        assert result.error is None
        assert result.execution_time > 0
        assert result.parameters == {"message": "hello world"}
    
    def test_registry_execute_tool_failure(self):
        """Test tool execution error handling."""
        # Setup
        registry = ToolSetRegistry()
        registry.register_tool_set(
            tool_set_name="test",
            description="Test tools",
            tool_classes=[FailingMockTool]
        )
        
        # Create tool call
        tool_call = ToolCall(
            tool_name="failing_tool",
            arguments={"input": "test"}
        )
        
        # Execute
        result = registry.execute_tool(tool_call)
        
        # Verify
        assert isinstance(result, ToolExecutionResult)
        assert result.tool_name == "failing_tool"
        assert result.success is False
        assert result.result is None
        assert "This tool always fails" in result.error
        assert result.execution_time > 0
        assert result.parameters == {"input": "test"}
    
    def test_registry_unknown_tool(self):
        """Test handling of unknown tool."""
        # Setup
        registry = ToolSetRegistry()
        
        # Create tool call for unknown tool
        tool_call = ToolCall(
            tool_name="unknown_tool",
            arguments={"param": "value"}
        )
        
        # Execute
        result = registry.execute_tool(tool_call)
        
        # Verify
        assert isinstance(result, ToolExecutionResult)
        assert result.tool_name == "unknown_tool"
        assert result.success is False
        assert result.result is None
        assert "Unknown tool: unknown_tool" in result.error
        assert result.execution_time >= 0
        assert result.parameters == {"param": "value"}
    
    def test_activity_manager_with_registry(self):
        """Test ActivityManager using ToolSetRegistry."""
        # Setup registry with tools
        registry = ToolSetRegistry()
        registry.register_tool_set(
            tool_set_name="test",
            description="Test tools",
            tool_classes=[MockTool]
        )
        
        # Create a simple mock agent loop
        class MockAgentLoop:
            def __init__(self):
                pass
            
            def get_next_action(self, conversation_state):
                from shared.models import ActionDecision, ActionType, ToolCall
                
                # Always return a final response on first call
                return ActionDecision(
                    action_type=ActionType.FINAL_RESPONSE,
                    reasoning="Test complete",
                    tool_calls=[],
                    final_response="Test completed successfully",
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
        assert "mock_tool" in tools
        
        # Test running activity
        result = activity_manager.run_activity(
            user_query="Test query",
            goal="Test goal"
        )
        
        # Verify
        assert result.status == "completed"
        assert result.final_response == "Test completed successfully"
        assert result.total_iterations == 1
        assert result.total_tool_calls == 0
    
    def test_activity_manager_tool_execution(self):
        """Test ActivityManager actually executing tools."""
        # Setup registry with tools
        registry = ToolSetRegistry()
        registry.register_tool_set(
            tool_set_name="test",
            description="Test tools",
            tool_classes=[MockTool]
        )
        
        # Create a mock agent loop that executes a tool
        class MockAgentLoopWithTool:
            def __init__(self):
                self.call_count = 0
            
            def get_next_action(self, conversation_state):
                from shared.models import ActionDecision, ActionType, ToolCall
                
                self.call_count += 1
                
                if self.call_count == 1:
                    # First call - execute tool
                    return ActionDecision(
                        action_type=ActionType.TOOL_EXECUTION,
                        reasoning="Need to execute mock tool",
                        tool_calls=[
                            ToolCall(
                                tool_name="mock_tool",
                                arguments={"message": "test execution"}
                            )
                        ],
                        final_response=None,
                        should_continue=False  # Don't continue after tool execution
                    )
                else:
                    # Second call - return final response
                    return ActionDecision(
                        action_type=ActionType.FINAL_RESPONSE,
                        reasoning="All done",
                        tool_calls=[],
                        final_response="Tool execution completed",
                        should_continue=False
                    )
        
        # Create activity manager
        agent_loop = MockAgentLoopWithTool()
        activity_manager = ActivityManager(
            agent_loop=agent_loop,
            tool_registry=registry,
            max_iterations=3,
            timeout_seconds=10.0
        )
        
        # Test running activity
        result = activity_manager.run_activity(
            user_query="Execute mock tool",
            goal="Test tool execution"
        )
        
        # Verify
        assert result.status == "completed"
        assert result.total_iterations == 1
        assert result.total_tool_calls == 1
        assert result.tools_used == ["mock_tool"]
        assert len(result.errors_encountered) == 0
    
    def test_explicit_registration_pattern(self):
        """Test explicit registration pattern without decorators."""
        # Create a fresh registry
        registry = ToolSetRegistry()
        
        # Define a test tool
        class ExplicitTool(BaseTool):
            NAME = "explicit_tool"
            MODULE = "test"
            
            def __init__(self):
                super().__init__(
                    description="An explicitly registered tool",
                    arguments=[
                        ToolArgument(
                            name="value",
                            type="str", 
                            description="Test value",
                            required=True
                        )
                    ]
                )
            
            def execute(self, **kwargs) -> Dict[str, Any]:
                return {"explicit_result": kwargs.get("value", "default")}
        
        # Register explicitly
        registry.register_tool_set(
            tool_set_name="explicit_test",
            description="Explicitly registered tools",
            tool_classes=[ExplicitTool]
        )
        
        # Test tool is registered
        assert "explicit_tool" in registry.get_tool_names()
        
        # Test tool can be executed
        tool_call = ToolCall(
            tool_name="explicit_tool",
            arguments={"value": "test_value"}
        )
        
        result = registry.execute_tool(tool_call)
        assert result.success is True
        assert result.result == {"explicit_result": "test_value"}
    
    def test_tool_set_isolation(self):
        """Test that tool sets are properly isolated."""
        # Create two registries
        registry1 = ToolSetRegistry()
        registry2 = ToolSetRegistry()
        
        # Register different tools in each
        registry1.register_tool_set(
            tool_set_name="set1",
            description="Tool set 1",
            tool_classes=[MockTool]
        )
        
        registry2.register_tool_set(
            tool_set_name="set2", 
            description="Tool set 2",
            tool_classes=[FailingMockTool]
        )
        
        # Verify isolation
        assert "mock_tool" in registry1.get_tool_names()
        assert "failing_tool" in registry2.get_tool_names()
        assert "failing_tool" not in registry1.get_tool_names()
        assert "mock_tool" not in registry2.get_tool_names()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])