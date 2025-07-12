"""
Tests for Phase 7: Response Formatting and Conversation History

This module tests the ResponseFormatter and ConversationManager modules
including different response styles, conversation history management,
and DSPy integration.
"""

import pytest
import time
from unittest.mock import Mock, patch
from agentic_loop.response_formatter import (
    ResponseFormatter, ConversationManager, ResponseStyle
)
from shared.models import ConversationEntry, ToolExecutionResult, ToolCall


class TestResponseFormatter:
    """Test suite for ResponseFormatter module."""
    
    def test_response_formatter_init(self):
        """Test ResponseFormatter initialization."""
        formatter = ResponseFormatter()
        assert formatter.default_style == ResponseStyle.DETAILED
        
        formatter_concise = ResponseFormatter(ResponseStyle.CONCISE)
        assert formatter_concise.default_style == ResponseStyle.CONCISE
    
    def test_format_tool_results_empty(self):
        """Test formatting empty tool results."""
        formatter = ResponseFormatter()
        result = formatter._format_tool_results([])
        assert result == "No tool results available"
    
    def test_format_tool_results_success(self):
        """Test formatting successful tool results."""
        formatter = ResponseFormatter()
        
        tool_results = [
            ToolExecutionResult(
                tool_name="test_tool",
                success=True,
                result={"message": "Success!"},
                error=None
            )
        ]
        
        result = formatter._format_tool_results(tool_results)
        assert "test_tool" in result
        assert "✅ Success" in result
        assert "Success!" in result
        assert "Error: None" in result
    
    def test_format_tool_results_failure(self):
        """Test formatting failed tool results."""
        formatter = ResponseFormatter()
        
        tool_results = [
            ToolExecutionResult(
                tool_name="failing_tool",
                success=False,
                result=None,
                error="Tool execution failed"
            )
        ]
        
        result = formatter._format_tool_results(tool_results)
        assert "failing_tool" in result
        assert "❌ Failed" in result
        assert "Tool execution failed" in result
    
    def test_format_tool_results_mixed(self):
        """Test formatting mixed success/failure tool results."""
        formatter = ResponseFormatter()
        
        tool_results = [
            ToolExecutionResult(
                tool_name="success_tool",
                success=True,
                result={"data": "good"},
                error=None
            ),
            ToolExecutionResult(
                tool_name="fail_tool",
                success=False,
                result=None,
                error="Failed to execute"
            )
        ]
        
        result = formatter._format_tool_results(tool_results)
        assert "success_tool" in result
        assert "✅ Success" in result
        assert "fail_tool" in result
        assert "❌ Failed" in result
        assert "Failed to execute" in result
    
    def test_format_conversation_entries_empty(self):
        """Test formatting empty conversation entries."""
        formatter = ResponseFormatter()
        result = formatter._format_conversation_entries([])
        assert result == "No conversation history available"
    
    def test_format_conversation_entries_with_tools(self):
        """Test formatting conversation entries with tools."""
        formatter = ResponseFormatter()
        
        entries = [
            ConversationEntry(
                iteration=1,
                user_input="Test request",
                response="Test response",
                tool_calls_made=[
                    ToolCall(tool_name="test_tool", arguments={"arg": "value"})
                ],
                tool_results=[
                    ToolExecutionResult(
                        tool_name="test_tool",
                        success=True,
                        result={"output": "result"}
                    )
                ]
            )
        ]
        
        result = formatter._format_conversation_entries(entries)
        assert "Iteration 1:" in result
        assert "Test request" in result
        assert "Test response" in result
        assert "Tools used: test_tool" in result
    
    def test_format_conversation_entries_no_tools(self):
        """Test formatting conversation entries without tools."""
        formatter = ResponseFormatter()
        
        entries = [
            ConversationEntry(
                iteration=1,
                user_input="Simple request",
                response="Simple response",
                tool_calls_made=[],
                tool_results=[]
            )
        ]
        
        result = formatter._format_conversation_entries(entries)
        assert "Iteration 1:" in result
        assert "Simple request" in result
        assert "Simple response" in result
        assert "No tools used" in result
    
    def test_interpret_confidence_high(self):
        """Test confidence interpretation for high confidence."""
        formatter = ResponseFormatter()
        
        # Mock the confidence interpreter
        with patch.object(formatter, 'confidence_interpreter') as mock_interpreter:
            mock_result = Mock()
            mock_result.confidence_level = "High"
            mock_result.explanation = "Very confident"
            mock_interpreter.return_value = mock_result
            
            result = formatter.interpret_confidence(0.9)
            assert result["level"] == "High"
            assert result["explanation"] == "Very confident"
    
    def test_interpret_confidence_fallback(self):
        """Test confidence interpretation fallback logic."""
        formatter = ResponseFormatter()
        
        # Mock the confidence interpreter to raise an exception
        with patch.object(formatter, 'confidence_interpreter', side_effect=Exception("Mock error")):
            # Test high confidence fallback
            result = formatter.interpret_confidence(0.9)
            assert result["level"] == "High"
            assert "Very confident" in result["explanation"]
            
            # Test medium confidence fallback
            result = formatter.interpret_confidence(0.7)
            assert result["level"] == "Medium"
            assert "Moderately confident" in result["explanation"]
            
            # Test low confidence fallback
            result = formatter.interpret_confidence(0.3)
            assert result["level"] == "Low"
            assert "Low confidence" in result["explanation"]
    
    @patch('agentic_loop.response_formatter.dspy.ChainOfThought')
    def test_forward_method_basic(self, mock_chain_of_thought):
        """Test the forward method with basic parameters."""
        # Mock DSPy components
        mock_result = Mock()
        mock_result.formatted_response = "Formatted response"
        mock_result.confidence_statement = "High confidence"
        mock_result.key_points = ["Point 1", "Point 2"]
        
        mock_predictor = Mock()
        mock_predictor.return_value = mock_result
        mock_chain_of_thought.return_value = mock_predictor
        
        formatter = ResponseFormatter()
        
        tool_results = [
            ToolExecutionResult(
                tool_name="test_tool",
                success=True,
                result={"data": "test"}
            )
        ]
        
        result = formatter.forward(
            raw_response="Raw response",
            tool_results=tool_results,
            confidence_score=0.8
        )
        
        # Verify the predictor was called
        mock_predictor.assert_called_once()
        call_args = mock_predictor.call_args[1]
        assert call_args["raw_response"] == "Raw response"
        assert call_args["response_style"] == ResponseStyle.DETAILED.value
        assert call_args["confidence_score"] == 0.8
        assert "test_tool" in call_args["tool_results"]
    
    @patch('agentic_loop.response_formatter.dspy.ChainOfThought')
    def test_format_conversation_summary(self, mock_chain_of_thought):
        """Test conversation summary formatting."""
        # Mock DSPy components
        mock_result = Mock()
        mock_result.summary = "Conversation summary"
        mock_result.key_insights = ["Insight 1", "Insight 2"]
        mock_result.relevant_context = "Relevant context"
        
        mock_predictor = Mock()
        mock_predictor.return_value = mock_result
        mock_chain_of_thought.return_value = mock_predictor
        
        formatter = ResponseFormatter()
        
        entries = [
            ConversationEntry(
                iteration=1,
                user_input="Test query",
                response="Test response",
                tool_calls_made=[],
                tool_results=[]
            )
        ]
        
        result = formatter.format_conversation_summary(entries, "Current query")
        
        # Verify the predictor was called
        mock_predictor.assert_called_once()
        call_args = mock_predictor.call_args[1]
        assert call_args["focus_query"] == "Current query"
        assert "Test query" in call_args["conversation_entries"]


class TestConversationManager:
    """Test suite for ConversationManager module."""
    
    def test_conversation_manager_init(self):
        """Test ConversationManager initialization."""
        manager = ConversationManager()
        assert manager.max_history_length == 10
        assert manager.auto_summarize_threshold == 20
        
        manager_custom = ConversationManager(max_history_length=5, auto_summarize_threshold=15)
        assert manager_custom.max_history_length == 5
        assert manager_custom.auto_summarize_threshold == 15
    
    def test_add_conversation_entry_basic(self):
        """Test adding a basic conversation entry."""
        manager = ConversationManager()
        
        existing_entries = []
        new_entry = ConversationEntry(
            iteration=1,
            user_input="Test input",
            response="Test response",
            tool_calls_made=[],
            tool_results=[]
        )
        
        updated_entries = manager.add_conversation_entry(existing_entries, new_entry)
        
        assert len(updated_entries) == 1
        assert updated_entries[0] == new_entry
    
    def test_add_conversation_entry_truncation(self):
        """Test conversation entry truncation when exceeding max length."""
        manager = ConversationManager(max_history_length=2, auto_summarize_threshold=5)
        
        # Create entries that exceed max length but not auto-summarize threshold
        existing_entries = [
            ConversationEntry(
                iteration=i,
                user_input=f"Input {i}",
                response=f"Response {i}",
                tool_calls_made=[],
                tool_results=[]
            )
            for i in range(1, 4)  # 3 entries
        ]
        
        new_entry = ConversationEntry(
            iteration=4,
            user_input="Input 4",
            response="Response 4",
            tool_calls_made=[],
            tool_results=[]
        )
        
        updated_entries = manager.add_conversation_entry(existing_entries, new_entry)
        
        # Should keep only the last 2 entries
        assert len(updated_entries) == 2
        assert updated_entries[0].iteration == 3
        assert updated_entries[1].iteration == 4
    
    def test_format_history_for_llm(self):
        """Test formatting history for LLM consumption."""
        manager = ConversationManager()
        
        entries = [
            ConversationEntry(
                iteration=1,
                user_input="Test question",
                response="Test answer",
                tool_calls_made=[
                    ToolCall(tool_name="search", arguments={"query": "test"})
                ],
                tool_results=[]
            )
        ]
        
        result = manager.format_history_for_llm(entries)
        
        assert "Iteration 1:" in result
        assert "Test question" in result
        assert "Test answer" in result
        assert "Tools used: search" in result
    
    def test_format_history_for_human_empty(self):
        """Test formatting empty history for human reading."""
        manager = ConversationManager()
        
        result = manager.format_history_for_human([])
        assert result == "No conversation history available."
    
    def test_format_history_for_human_with_tools(self):
        """Test formatting history for human reading with tools."""
        manager = ConversationManager()
        
        entries = [
            ConversationEntry(
                iteration=1,
                user_input="Test request",
                response="Test response",
                tool_calls_made=[
                    ToolCall(tool_name="calculator", arguments={"expression": "2+2"})
                ],
                tool_results=[
                    ToolExecutionResult(
                        tool_name="calculator",
                        success=True,
                        result={"answer": 4}
                    )
                ],
                timestamp=time.time()
            )
        ]
        
        result = manager.format_history_for_human(entries)
        
        assert "Iteration 1:" in result
        assert "👤 User: Test request" in result
        assert "🤖 Agent: Test response" in result
        assert "📱 Tools used: calculator" in result
        assert "✅ Successful: calculator" in result
    
    def test_format_history_for_human_with_failed_tools(self):
        """Test formatting history for human reading with failed tools."""
        manager = ConversationManager()
        
        entries = [
            ConversationEntry(
                iteration=1,
                user_input="Test request",
                response="Test response",
                tool_calls_made=[
                    ToolCall(tool_name="broken_tool", arguments={})
                ],
                tool_results=[
                    ToolExecutionResult(
                        tool_name="broken_tool",
                        success=False,
                        result=None,
                        error="Tool failed"
                    )
                ],
                timestamp=time.time()
            )
        ]
        
        result = manager.format_history_for_human(entries)
        
        assert "❌ Failed: broken_tool" in result
    
    def test_get_conversation_stats_empty(self):
        """Test conversation statistics for empty history."""
        manager = ConversationManager()
        
        stats = manager.get_conversation_stats([])
        
        assert stats["total_iterations"] == 0
        assert stats["total_tools_used"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["most_used_tools"] == []
        assert stats["average_response_length"] == 0
    
    def test_get_conversation_stats_with_data(self):
        """Test conversation statistics with actual data."""
        manager = ConversationManager()
        
        entries = [
            ConversationEntry(
                iteration=1,
                user_input="First request",
                response="First response (20 chars)",
                tool_calls_made=[
                    ToolCall(tool_name="search", arguments={"query": "test"})
                ],
                tool_results=[
                    ToolExecutionResult(
                        tool_name="search",
                        success=True,
                        result={"results": []}
                    )
                ]
            ),
            ConversationEntry(
                iteration=2,
                user_input="Second request",
                response="Second response",
                tool_calls_made=[
                    ToolCall(tool_name="search", arguments={"query": "test2"}),
                    ToolCall(tool_name="calculator", arguments={"expr": "1+1"})
                ],
                tool_results=[
                    ToolExecutionResult(
                        tool_name="search",
                        success=True,
                        result={"results": []}
                    ),
                    ToolExecutionResult(
                        tool_name="calculator",
                        success=False,
                        result=None,
                        error="Error"
                    )
                ]
            )
        ]
        
        stats = manager.get_conversation_stats(entries)
        
        assert stats["total_iterations"] == 2
        assert stats["total_tools_used"] == 3
        assert stats["success_rate"] == 2/3  # 2 successful out of 3 total
        assert stats["most_used_tools"][0] == ("search", 2)  # search used twice
        assert stats["average_response_length"] > 0
    
    @patch('agentic_loop.response_formatter.dspy.ChainOfThought')
    def test_compress_history_basic(self, mock_chain_of_thought):
        """Test basic history compression."""
        # Mock DSPy components
        mock_result = Mock()
        mock_result.compressed_history = "Compressed summary"
        mock_result.preserved_context = "Important context"
        
        mock_predictor = Mock()
        mock_predictor.return_value = mock_result
        mock_chain_of_thought.return_value = mock_predictor
        
        manager = ConversationManager(max_history_length=2)
        
        # Create entries that exceed max length
        entries = [
            ConversationEntry(
                iteration=i,
                user_input=f"Input {i}",
                response=f"Response {i}",
                tool_calls_made=[],
                tool_results=[]
            )
            for i in range(1, 6)  # 5 entries
        ]
        
        compressed_entries = manager._compress_history(entries)
        
        # Should have 3 entries: 1 summary + 2 recent
        assert len(compressed_entries) == 3
        assert compressed_entries[0].iteration == 0  # Summary entry
        assert compressed_entries[0].user_input == "[COMPRESSED HISTORY]"
        assert "Compressed summary" in compressed_entries[0].response
        assert compressed_entries[1].iteration == 4  # Recent entry
        assert compressed_entries[2].iteration == 5  # Most recent entry
    
    @patch('agentic_loop.response_formatter.dspy.ChainOfThought')
    def test_compress_history_fallback(self, mock_chain_of_thought):
        """Test history compression fallback on error."""
        # Mock DSPy components to raise an exception
        mock_predictor = Mock()
        mock_predictor.side_effect = Exception("Mock compression error")
        mock_chain_of_thought.return_value = mock_predictor
        
        manager = ConversationManager(max_history_length=2)
        
        # Create entries that exceed max length
        entries = [
            ConversationEntry(
                iteration=i,
                user_input=f"Input {i}",
                response=f"Response {i}",
                tool_calls_made=[],
                tool_results=[]
            )
            for i in range(1, 6)  # 5 entries
        ]
        
        compressed_entries = manager._compress_history(entries)
        
        # Should fallback to simple truncation (last 2 entries)
        assert len(compressed_entries) == 2
        assert compressed_entries[0].iteration == 4
        assert compressed_entries[1].iteration == 5
    
    def test_compress_history_no_compression_needed(self):
        """Test that compression is skipped when not needed."""
        manager = ConversationManager(max_history_length=5)
        
        entries = [
            ConversationEntry(
                iteration=i,
                user_input=f"Input {i}",
                response=f"Response {i}",
                tool_calls_made=[],
                tool_results=[]
            )
            for i in range(1, 4)  # 3 entries (under limit)
        ]
        
        result = manager._compress_history(entries)
        
        # Should return original entries unchanged
        assert len(result) == 3
        assert result == entries


class TestResponseStyles:
    """Test suite for response style enumeration."""
    
    def test_response_style_enum_values(self):
        """Test ResponseStyle enum values."""
        assert ResponseStyle.DETAILED.value == "detailed"
        assert ResponseStyle.CONCISE.value == "concise"
        assert ResponseStyle.SUMMARY.value == "summary"
        assert ResponseStyle.TECHNICAL.value == "technical"
    
    def test_response_style_enum_iteration(self):
        """Test that all response styles can be iterated."""
        styles = list(ResponseStyle)
        assert len(styles) == 4
        assert ResponseStyle.DETAILED in styles
        assert ResponseStyle.CONCISE in styles
        assert ResponseStyle.SUMMARY in styles
        assert ResponseStyle.TECHNICAL in styles


class TestIntegrationScenarios:
    """Test integration scenarios between ResponseFormatter and ConversationManager."""
    
    def test_end_to_end_conversation_flow(self):
        """Test end-to-end conversation flow with formatting."""
        manager = ConversationManager()
        formatter = ResponseFormatter()
        
        # Create a conversation entry
        entry = ConversationEntry(
            iteration=1,
            user_input="What is 2+2?",
            response="The answer is 4",
            tool_calls_made=[
                ToolCall(tool_name="calculator", arguments={"expression": "2+2"})
            ],
            tool_results=[
                ToolExecutionResult(
                    tool_name="calculator",
                    success=True,
                    result={"answer": 4}
                )
            ]
        )
        
        # Add to conversation history
        updated_entries = manager.add_conversation_entry([], entry)
        
        # Format for human consumption
        human_format = manager.format_history_for_human(updated_entries)
        
        # Format for LLM consumption
        llm_format = manager.format_history_for_llm(updated_entries)
        
        # Verify both formats contain expected content
        assert "What is 2+2?" in human_format
        assert "The answer is 4" in human_format
        assert "calculator" in human_format
        
        assert "What is 2+2?" in llm_format
        assert "The answer is 4" in llm_format
        assert "calculator" in llm_format
    
    def test_conversation_stats_accuracy(self):
        """Test accuracy of conversation statistics."""
        manager = ConversationManager()
        
        # Create diverse conversation entries
        entries = [
            ConversationEntry(
                iteration=1,
                user_input="Search for Python",
                response="Found Python information",
                tool_calls_made=[
                    ToolCall(tool_name="search", arguments={"query": "Python"})
                ],
                tool_results=[
                    ToolExecutionResult(tool_name="search", success=True, result={"count": 100})
                ]
            ),
            ConversationEntry(
                iteration=2,
                user_input="Calculate 10 * 5",
                response="The result is 50",
                tool_calls_made=[
                    ToolCall(tool_name="calculator", arguments={"expression": "10*5"})
                ],
                tool_results=[
                    ToolExecutionResult(tool_name="calculator", success=True, result={"answer": 50})
                ]
            ),
            ConversationEntry(
                iteration=3,
                user_input="Try broken tool",
                response="Tool failed",
                tool_calls_made=[
                    ToolCall(tool_name="broken_tool", arguments={})
                ],
                tool_results=[
                    ToolExecutionResult(tool_name="broken_tool", success=False, error="Failed")
                ]
            )
        ]
        
        stats = manager.get_conversation_stats(entries)
        
        # Verify statistics
        assert stats["total_iterations"] == 3
        assert stats["total_tools_used"] == 3
        assert stats["success_rate"] == 2/3  # 2 successful out of 3
        
        # Verify most used tools (all used once, so order may vary)
        tool_names = [tool_name for tool_name, count in stats["most_used_tools"]]
        assert "search" in tool_names
        assert "calculator" in tool_names
        assert "broken_tool" in tool_names
        
        # Verify average response length calculation
        expected_avg = (
            len("Found Python information") + 
            len("The result is 50") + 
            len("Tool failed")
        ) / 3
        assert abs(stats["average_response_length"] - expected_avg) < 0.1