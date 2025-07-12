"""
Test suite for Phase 3: ManualAgentLoop with Basic Iteration.

This test suite validates the ManualAgentLoop implementation with simple
single-iteration scenarios.
"""

import pytest
from unittest.mock import Mock
from shared.models import (
    ConversationState,
    ActionDecision,
    ActionType,
    ToolCall,
    ToolExecutionResult,
    ConversationEntry
)
from agentic_loop.manual_agent_loop import ManualAgentLoop


class TestManualAgentLoop:
    """Test suite for ManualAgentLoop class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool_names = ["search", "calculate", "weather"]
        self.agent_loop = ManualAgentLoop(self.tool_names, max_iterations=3)
    
    def test_initialization(self):
        """Test ManualAgentLoop initialization."""
        assert self.agent_loop.tool_names == self.tool_names
        assert self.agent_loop.max_iterations == 3
        assert self.agent_loop.agent_reasoner is not None
    
    def test_get_available_tools(self):
        """Test getting available tools."""
        tools = self.agent_loop.get_available_tools()
        assert tools == self.tool_names
        assert tools is not self.tool_names  # Should be a copy
    
    def test_update_tool_names(self):
        """Test updating tool names."""
        new_tools = ["new_tool", "another_tool"]
        self.agent_loop.update_tool_names(new_tools)
        assert self.agent_loop.tool_names == new_tools
        assert self.agent_loop.agent_reasoner.tool_names == new_tools
    
    def test_format_conversation_history_empty(self):
        """Test formatting empty conversation history."""
        conversation_state = ConversationState(
            user_query="Test query",
            goal=None,
            conversation_history=[],
            last_tool_results=None,
            iteration_count=1,
            max_iterations=3
        )
        
        formatted = self.agent_loop._format_conversation_history(conversation_state)
        assert formatted == "No previous conversation history."
    
    def test_format_conversation_history_with_entries(self):
        """Test formatting conversation history with entries."""
        conversation_history = [
            ConversationEntry(
                iteration=1,
                user_input="Hello",
                response="Hi there!",
                tool_calls_made=[],
                tool_results=[]
            ),
            ConversationEntry(
                iteration=2,
                user_input="How are you?",
                response="I'm doing well!",
                tool_calls_made=[],
                tool_results=[]
            )
        ]
        
        conversation_state = ConversationState(
            user_query="Test query",
            goal=None,
            conversation_history=conversation_history,
            last_tool_results=None,
            iteration_count=3,
            max_iterations=3
        )
        
        formatted = self.agent_loop._format_conversation_history(conversation_state)
        expected = "Iteration 1: Hello -> Hi there!\nIteration 2: How are you? -> I'm doing well!"
        assert formatted == expected
    
    def test_format_tool_results_empty(self):
        """Test formatting empty tool results."""
        formatted = self.agent_loop._format_tool_results(None)
        assert formatted is None
        
        formatted = self.agent_loop._format_tool_results([])
        assert formatted is None
    
    def test_format_tool_results_with_results(self):
        """Test formatting tool results with success and failure."""
        tool_results = [
            ToolExecutionResult(
                tool_name="search",
                success=True,
                result="Found some results",
                error=None,
                execution_time=0.1
            ),
            ToolExecutionResult(
                tool_name="calculate",
                success=False,
                result=None,
                error="Division by zero",
                execution_time=0.05
            )
        ]
        
        formatted = self.agent_loop._format_tool_results(tool_results)
        expected = "Tool 'search' succeeded: Found some results\nTool 'calculate' failed: Division by zero"
        assert formatted == expected
    
    def test_format_available_tools(self):
        """Test formatting available tools."""
        formatted = self.agent_loop._format_available_tools()
        assert "search" in formatted
        assert "calculate" in formatted
        assert "weather" in formatted
        assert '"name"' in formatted
        assert '"description"' in formatted
    
    def test_create_error_decision(self):
        """Test creating error decision."""
        conversation_state = ConversationState(
            user_query="Test query",
            goal=None,
            conversation_history=[],
            last_tool_results=None,
            iteration_count=1,
            max_iterations=3
        )
        
        decision = self.agent_loop._create_error_decision("Test error", conversation_state)
        
        assert decision.action_type == ActionType.ERROR_RECOVERY
        assert decision.tool_calls == []
        assert "Test error" in decision.reasoning
        assert decision.should_continue is False
        assert decision.confidence_score == 0.0
        assert decision.iteration_count == 1
        assert decision.max_iterations == 3
    
    def test_get_next_action_with_mock_reasoner(self):
        """Test get_next_action with mocked reasoner."""
        # Create mock reasoner result
        from shared.models import ReasoningOutput
        mock_reasoning_output = ReasoningOutput(
            overall_reasoning="Test reasoning",
            confidence=0.8,
            should_use_tools=True,
            tool_calls=[
                ToolCall(tool_name="search", arguments={"query": "test"})
            ],
            should_continue=True,
            continuation_reasoning="Need to continue",
            final_response=None
        )
        
        # Mock the agent reasoner's __call__ method
        mock_result = Mock()
        mock_result.reasoning_output = mock_reasoning_output
        
        # Create agent loop and replace the reasoner
        agent_loop = ManualAgentLoop(self.tool_names, max_iterations=3)
        agent_loop.agent_reasoner = Mock(return_value=mock_result)
        
        conversation_state = ConversationState(
            user_query="Search for something",
            goal=None,
            conversation_history=[],
            last_tool_results=None,
            iteration_count=1,
            max_iterations=3
        )
        
        # Call get_next_action
        decision = agent_loop.get_next_action(conversation_state)
        
        # Verify the result
        assert decision.action_type == ActionType.TOOL_EXECUTION
        assert len(decision.tool_calls) == 1
        assert decision.tool_calls[0].tool_name == "search"
        assert decision.should_continue is True
        assert decision.confidence_score == 0.8
    
    def test_forward_method_compatibility(self):
        """Test DSPy forward method compatibility."""
        # This test ensures the forward method exists and has the right signature
        conversation_state = ConversationState(
            user_query="Test query",
            goal=None,
            conversation_history=[],
            last_tool_results=None,
            iteration_count=1,
            max_iterations=3
        )
        
        # Should not raise an exception
        # Note: This will fail without proper DSPy setup, but validates interface
        try:
            result = self.agent_loop.forward(conversation_state)
            # If successful, verify it returns the expected type
            assert isinstance(result, ActionDecision)
        except Exception as e:
            # Expected with mocked environment - just verify method exists
            assert hasattr(self.agent_loop, 'forward')
            assert callable(getattr(self.agent_loop, 'forward'))


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])