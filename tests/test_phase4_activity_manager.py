"""
Test suite for Phase 4: ActivityManager for External Control.

This test suite validates the ActivityManager implementation with mock
agents and tool registries.
"""

import pytest
from unittest.mock import Mock, MagicMock
from shared.models import (
    ConversationState,
    ActionDecision,
    ActionType,
    ToolCall,
    ToolExecutionResult,
    ActivityResult,
    ReasoningOutput
)
from agentic_loop.manual_agent_loop import ManualAgentLoop
from agentic_loop.activity_manager import ActivityManager


class TestActivityManager:
    """Test suite for ActivityManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool_names = ["search", "calculate", "weather"]
        
        # Create mock agent loop
        self.mock_agent_loop = Mock(spec=ManualAgentLoop)
        self.mock_agent_loop.get_available_tools.return_value = self.tool_names
        
        # Create mock tool registry
        self.mock_tool_registry = Mock()
        self.mock_tool_registry.get_tool_names.return_value = self.tool_names
        
        # Create activity manager
        self.activity_manager = ActivityManager(
            agent_loop=self.mock_agent_loop,
            tool_registry=self.mock_tool_registry,
            max_iterations=3,
            timeout_seconds=10.0
        )
    
    def test_initialization(self):
        """Test ActivityManager initialization."""
        assert self.activity_manager.agent_loop == self.mock_agent_loop
        assert self.activity_manager.tool_registry == self.mock_tool_registry
        assert self.activity_manager.max_iterations == 3
        assert self.activity_manager.timeout_seconds == 10.0
    
    def test_get_available_tools(self):
        """Test getting available tools."""
        tools = self.activity_manager.get_available_tools()
        assert tools == self.tool_names
        self.mock_tool_registry.get_tool_names.assert_called_once()
    
    def test_update_configuration(self):
        """Test updating configuration."""
        self.activity_manager.update_configuration(
            max_iterations=5,
            timeout_seconds=30.0
        )
        assert self.activity_manager.max_iterations == 5
        assert self.activity_manager.timeout_seconds == 30.0
    
    def test_run_activity_immediate_final_response(self):
        """Test activity that returns final response immediately."""
        # Mock agent to return final response
        mock_decision = ActionDecision(
            action_type=ActionType.FINAL_RESPONSE,
            tool_calls=[],
            reasoning="Task completed",
            should_continue=False,
            final_response="Here's your answer!",
            confidence_score=0.9,
            iteration_count=1,
            max_iterations=3
        )
        self.mock_agent_loop.get_next_action.return_value = mock_decision
        
        # Run activity
        result = self.activity_manager.run_activity("Test query")
        
        # Verify result
        assert isinstance(result, ActivityResult)
        assert result.status == "completed"
        assert result.final_response == "Here's your answer!"
        assert result.total_iterations == 1
        assert result.total_tool_calls == 0
        assert len(result.tools_used) == 0
        assert result.conversation_state.iteration_count == 1
    
    def test_run_activity_with_tool_execution(self):
        """Test activity with tool execution."""
        # Mock tool call and result
        tool_call = ToolCall(tool_name="search", arguments={"query": "test"})
        tool_result = ToolExecutionResult(
            tool_name="search",
            success=True,
            result="Found results",
            error=None,
            execution_time=0.1
        )
        
        # Mock agent decisions
        tool_decision = ActionDecision(
            action_type=ActionType.TOOL_EXECUTION,
            tool_calls=[tool_call],
            reasoning="Need to search",
            should_continue=False,  # Stop after tools
            final_response="Search completed",
            confidence_score=0.8,
            iteration_count=1,
            max_iterations=3
        )
        
        self.mock_agent_loop.get_next_action.return_value = tool_decision
        self.mock_tool_registry.execute_tool.return_value = tool_result
        
        # Run activity
        result = self.activity_manager.run_activity("Search for something")
        
        # Verify result
        assert result.status == "completed"
        assert result.total_tool_calls == 1
        assert "search" in result.tools_used
        assert len(result.conversation_state.conversation_history) == 1
        
        # Verify tool executor was called
        self.mock_tool_registry.execute_tool.assert_called_once_with(tool_call)
    
    def test_run_activity_with_multiple_iterations(self):
        """Test activity with multiple iterations."""
        # Setup multiple decisions
        tool_call1 = ToolCall(tool_name="search", arguments={"query": "test"})
        tool_call2 = ToolCall(tool_name="calculate", arguments={"expression": "2+2"})
        
        tool_result1 = ToolExecutionResult(
            tool_name="search",
            success=True,
            result="Found results",
            error=None,
            execution_time=0.1
        )
        tool_result2 = ToolExecutionResult(
            tool_name="calculate",
            success=True,
            result="4",
            error=None,
            execution_time=0.05
        )
        
        # First iteration - tool execution, continue
        decision1 = ActionDecision(
            action_type=ActionType.TOOL_EXECUTION,
            tool_calls=[tool_call1],
            reasoning="Need to search first",
            should_continue=True,
            final_response=None,
            confidence_score=0.8,
            iteration_count=1,
            max_iterations=3
        )
        
        # Second iteration - tool execution, final
        decision2 = ActionDecision(
            action_type=ActionType.TOOL_EXECUTION,
            tool_calls=[tool_call2],
            reasoning="Now calculate result",
            should_continue=False,
            final_response="Task completed",
            confidence_score=0.9,
            iteration_count=2,
            max_iterations=3
        )
        
        # Mock agent to return different decisions
        self.mock_agent_loop.get_next_action.side_effect = [decision1, decision2]
        self.mock_tool_registry.execute_tool.side_effect = [tool_result1, tool_result2]
        
        # Run activity
        result = self.activity_manager.run_activity("Multi-step task")
        
        # Verify result
        assert result.status == "completed"
        assert result.total_iterations == 2
        assert result.total_tool_calls == 2
        assert set(result.tools_used) == {"search", "calculate"}
        assert len(result.conversation_state.conversation_history) == 2
    
    def test_run_activity_with_tool_error(self):
        """Test activity with tool execution error."""
        # Mock tool call and error result
        tool_call = ToolCall(tool_name="search", arguments={"query": "test"})
        tool_result = ToolExecutionResult(
            tool_name="search",
            success=False,
            result=None,
            error="Network error",
            execution_time=0.1
        )
        
        # Mock agent decision
        tool_decision = ActionDecision(
            action_type=ActionType.TOOL_EXECUTION,
            tool_calls=[tool_call],
            reasoning="Need to search",
            should_continue=False,
            final_response="Search attempted",
            confidence_score=0.8,
            iteration_count=1,
            max_iterations=3
        )
        
        self.mock_agent_loop.get_next_action.return_value = tool_decision
        self.mock_tool_registry.execute_tool.return_value = tool_result
        
        # Run activity
        result = self.activity_manager.run_activity("Search for something")
        
        # Verify result
        assert result.status == "completed"
        assert result.total_tool_calls == 1
        assert "search" in result.tools_used
        assert len(result.errors_encountered) == 1
        assert "Network error" in result.errors_encountered[0]
    
    def test_run_activity_error_recovery(self):
        """Test activity with error recovery."""
        # Mock agent to return error recovery
        error_decision = ActionDecision(
            action_type=ActionType.ERROR_RECOVERY,
            tool_calls=[],
            reasoning="Something went wrong",
            should_continue=False,
            final_response="Error occurred",
            confidence_score=0.1,
            iteration_count=1,
            max_iterations=3
        )
        
        self.mock_agent_loop.get_next_action.return_value = error_decision
        
        # Run activity
        result = self.activity_manager.run_activity("Error test")
        
        # Verify result
        assert result.status == "error_recovery"
        assert "Something went wrong" in result.final_response
        assert result.total_iterations == 1
        assert result.total_tool_calls == 0
    
    def test_run_activity_max_iterations(self):
        """Test activity that reaches max iterations."""
        # Mock agent to always continue with goal check
        continue_decision = ActionDecision(
            action_type=ActionType.GOAL_CHECK,
            tool_calls=[],
            reasoning="Keep going",
            should_continue=True,
            final_response=None,
            confidence_score=0.5,
            iteration_count=1,
            max_iterations=3
        )
        
        self.mock_agent_loop.get_next_action.return_value = continue_decision
        
        # Run activity
        result = self.activity_manager.run_activity("Long task")
        
        # Verify result
        assert result.status == "max_iterations"
        assert result.total_iterations == 3  # Should hit max
        assert "maximum iterations" in result.final_response
    
    def test_run_activity_with_exception(self):
        """Test activity with unexpected exception."""
        # Mock agent to raise exception
        self.mock_agent_loop.get_next_action.side_effect = Exception("Unexpected error")
        
        # Run activity
        result = self.activity_manager.run_activity("Error test")
        
        # Verify result
        assert result.status == "error_recovery"
        assert "Unexpected error" in result.final_response
        assert result.total_iterations == 1
        assert len(result.errors_encountered) == 1
    
    def test_execute_tools_sequential_success(self):
        """Test sequential tool execution with success."""
        tool_calls = [
            ToolCall(tool_name="search", arguments={"query": "test"}),
            ToolCall(tool_name="calculate", arguments={"expression": "2+2"})
        ]
        
        tool_results = [
            ToolExecutionResult(
                tool_name="search",
                success=True,
                result="Found results",
                error=None,
                execution_time=0.1
            ),
            ToolExecutionResult(
                tool_name="calculate",
                success=True,
                result="4",
                error=None,
                execution_time=0.05
            )
        ]
        
        self.mock_tool_registry.execute_tool.side_effect = tool_results
        
        # Execute tools
        results = self.activity_manager._execute_tools_sequential(tool_calls)
        
        # Verify results
        assert len(results) == 2
        assert results[0].tool_name == "search"
        assert results[1].tool_name == "calculate"
        assert all(r.success for r in results)
    
    def test_execute_tools_sequential_with_exception(self):
        """Test sequential tool execution with exception."""
        tool_calls = [
            ToolCall(tool_name="search", arguments={"query": "test"})
        ]
        
        # Mock tool executor to raise exception
        self.mock_tool_registry.execute_tool.side_effect = Exception("Tool failed")
        
        # Execute tools
        results = self.activity_manager._execute_tools_sequential(tool_calls)
        
        # Verify results
        assert len(results) == 1
        assert results[0].tool_name == "search"
        assert not results[0].success
        assert "Tool failed" in results[0].error
    
    def test_activity_with_custom_id(self):
        """Test activity with custom activity ID."""
        # Mock agent to return final response
        mock_decision = ActionDecision(
            action_type=ActionType.FINAL_RESPONSE,
            tool_calls=[],
            reasoning="Task completed",
            should_continue=False,
            final_response="Done",
            confidence_score=0.9,
            iteration_count=1,
            max_iterations=3
        )
        self.mock_agent_loop.get_next_action.return_value = mock_decision
        
        # Run activity with custom ID
        custom_id = "test-activity-123"
        result = self.activity_manager.run_activity(
            "Test query", 
            activity_id=custom_id
        )
        
        # Verify custom ID is used
        assert result.activity_id == custom_id
        assert result.conversation_state.activity_id == custom_id
    
    def test_activity_with_goal(self):
        """Test activity with explicit goal."""
        # Mock agent to return final response
        mock_decision = ActionDecision(
            action_type=ActionType.FINAL_RESPONSE,
            tool_calls=[],
            reasoning="Goal achieved",
            should_continue=False,
            final_response="Goal completed",
            confidence_score=0.9,
            iteration_count=1,
            max_iterations=3
        )
        self.mock_agent_loop.get_next_action.return_value = mock_decision
        
        # Run activity with goal
        result = self.activity_manager.run_activity(
            "Test query",
            goal="Find the answer"
        )
        
        # Verify goal is passed
        assert result.conversation_state.goal == "Find the answer"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])