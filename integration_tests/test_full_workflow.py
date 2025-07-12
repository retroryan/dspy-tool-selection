"""
Full workflow integration tests for the agentic loop.

This module tests the complete workflow from user query to final response
using real LLM models and tools.
"""

import os
import sys
import time
from typing import List, Dict, Any

# Add parent directory to path to import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integration_tests.test_framework import create_test_runner
from shared.tool_set_registry import create_productivity_tool_set_registry
from agentic_loop.activity_manager import ActivityManager
from agentic_loop.manual_agent_loop import ManualAgentLoop
from agentic_loop.agent_reasoner import AgentReasoner
from agentic_loop.response_formatter import ResponseFormatter, ResponseStyle
from shared.models import ConversationState, ConversationEntry
from shared_utils.llm_factory import setup_llm


class FullWorkflowTests:
    """Integration tests for the complete agentic loop workflow."""
    
    def __init__(self):
        self.test_runner = create_test_runner(verbose=True)
        
        # Load environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        
        # Setup LLM
        try:
            setup_llm()
            print("✅ LLM setup successful")
        except Exception as e:
            print(f"❌ LLM setup failed: {e}")
            raise
        
        # Create tool registry with productivity tools
        self.tool_registry = create_productivity_tool_set_registry()
        print(f"✅ Tool registry created with tools: {self.tool_registry.get_tool_names()}")
        
        # Create agent components
        self.agent_reasoner = AgentReasoner(
            tool_names=self.tool_registry.get_tool_names(),
            max_iterations=3
        )
        
        self.manual_agent_loop = ManualAgentLoop(
            tool_names=self.tool_registry.get_tool_names()
        )
        
        self.activity_manager = ActivityManager(
            agent_loop=self.manual_agent_loop,
            tool_registry=self.tool_registry,
            max_iterations=3,
            timeout_seconds=60.0
        )
        
        self.response_formatter = ResponseFormatter()
        
        print("✅ All components initialized successfully")
    
    def test_simple_reminder_workflow(self) -> Dict[str, Any]:
        """Test a simple reminder creation workflow."""
        query = "Remind me to submit the project report tomorrow at 2 PM"
        
        # Run the activity
        activity_result = self.activity_manager.run_activity(
            user_query=query,
            activity_id="test_reminder_001"
        )
        
        # Verify the activity completed successfully
        self.test_runner.assert_true(
            activity_result.success,
            f"Activity failed: {activity_result.error}"
        )
        
        # Verify we got a final response
        self.test_runner.assert_not_none(
            activity_result.final_response,
            "No final response received"
        )
        
        # Verify tools were used (should use set_reminder)
        self.test_runner.assert_greater_than(
            len(activity_result.tool_execution_results),
            0,
            "No tools were executed"
        )
        
        # Check that set_reminder was called
        tool_names_used = [result.tool_name for result in activity_result.tool_execution_results]
        self.test_runner.assert_contains(
            tool_names_used,
            "set_reminder",
            "set_reminder tool was not used"
        )
        
        # Verify at least one tool succeeded
        successful_tools = [result for result in activity_result.tool_execution_results if result.success]
        self.test_runner.assert_greater_than(
            len(successful_tools),
            0,
            "No tools executed successfully"
        )
        
        return {
            "query": query,
            "success": activity_result.success,
            "iterations": activity_result.iteration_count,
            "tools_used": tool_names_used,
            "final_response_length": len(activity_result.final_response) if activity_result.final_response else 0
        }
    
    def test_complex_multi_reminder_workflow(self) -> Dict[str, Any]:
        """Test a more complex workflow with multiple reminders."""
        query = "Set up reminders for my busy day: meeting at 9 AM, lunch with client at 12:30 PM, and gym session at 6 PM"
        
        # Run the activity
        activity_result = self.activity_manager.run_activity(
            user_query=query,
            activity_id="test_multi_reminder_001"
        )
        
        # Verify the activity completed successfully
        self.test_runner.assert_true(
            activity_result.success,
            f"Activity failed: {activity_result.error}"
        )
        
        # Verify we got a final response
        self.test_runner.assert_not_none(
            activity_result.final_response,
            "No final response received"
        )
        
        # Verify tools were used
        self.test_runner.assert_greater_than(
            len(activity_result.tool_execution_results),
            0,
            "No tools were executed"
        )
        
        # The LLM might use set_reminder multiple times or once with multiple items
        # Let's just verify set_reminder was used
        tool_names_used = [result.tool_name for result in activity_result.tool_execution_results]
        self.test_runner.assert_contains(
            tool_names_used,
            "set_reminder",
            "set_reminder tool was not used"
        )
        
        return {
            "query": query,
            "success": activity_result.success,
            "iterations": activity_result.iteration_count,
            "tools_used": tool_names_used,
            "tool_execution_count": len(activity_result.tool_execution_results),
            "final_response_length": len(activity_result.final_response) if activity_result.final_response else 0
        }
    
    def test_response_formatting_workflow(self) -> Dict[str, Any]:
        """Test response formatting with different styles."""
        query = "Create a reminder for my dentist appointment next Wednesday at 3 PM"
        
        # Run the activity
        activity_result = self.activity_manager.run_activity(
            user_query=query,
            activity_id="test_formatting_001"
        )
        
        # Verify basic success
        self.test_runner.assert_true(
            activity_result.success,
            f"Activity failed: {activity_result.error}"
        )
        
        # Test different response formatting styles
        styles_tested = {}
        
        for style in [ResponseStyle.DETAILED, ResponseStyle.CONCISE, ResponseStyle.TECHNICAL]:
            formatted_result = self.response_formatter.forward(
                raw_response=activity_result.final_response or "No response",
                tool_results=activity_result.tool_execution_results,
                response_style=style,
                confidence_score=0.8
            )
            
            # Verify formatting succeeded
            self.test_runner.assert_not_none(
                formatted_result.formatted_response,
                f"Formatting failed for style: {style}"
            )
            
            styles_tested[style.value] = len(formatted_result.formatted_response)
        
        return {
            "query": query,
            "success": activity_result.success,
            "styles_tested": styles_tested,
            "original_response_length": len(activity_result.final_response) if activity_result.final_response else 0
        }
    
    def test_conversation_history_workflow(self) -> Dict[str, Any]:
        """Test conversation history management across multiple interactions."""
        
        # Create a conversation state
        conversation_state = ConversationState(
            user_query="I need help with my daily schedule",
            goal="Organize daily schedule with reminders",
            iteration_count=0,
            conversation_history=[],
            last_tool_results=[]
        )
        
        # First interaction: Set morning reminder
        query1 = "Set a reminder for my morning standup meeting at 9 AM"
        result1 = self.activity_manager.run_activity(
            user_query=query1,
            activity_id="test_history_001",
            conversation_state=conversation_state
        )
        
        self.test_runner.assert_true(result1.success, "First interaction failed")
        
        # Add to conversation history
        entry1 = ConversationEntry(
            iteration=1,
            user_input=query1,
            response=result1.final_response or "",
            tool_calls_made=[],
            tool_results=result1.tool_execution_results
        )
        
        conversation_state.conversation_history.append(entry1)
        conversation_state.iteration_count += 1
        
        # Second interaction: Set afternoon reminder
        query2 = "Also set a reminder for my doctor appointment at 2 PM"
        result2 = self.activity_manager.run_activity(
            user_query=query2,
            activity_id="test_history_002",
            conversation_state=conversation_state
        )
        
        self.test_runner.assert_true(result2.success, "Second interaction failed")
        
        # Test conversation formatting
        formatted_history = self.response_formatter.format_conversation_summary(
            conversation_entries=conversation_state.conversation_history,
            focus_query=query2
        )
        
        self.test_runner.assert_not_none(
            formatted_history.summary,
            "Conversation summary failed"
        )
        
        return {
            "interactions": 2,
            "both_successful": result1.success and result2.success,
            "history_entries": len(conversation_state.conversation_history),
            "summary_length": len(formatted_history.summary),
            "total_tools_used": len(result1.tool_execution_results) + len(result2.tool_execution_results)
        }
    
    def test_error_handling_workflow(self) -> Dict[str, Any]:
        """Test error handling with an impossible request."""
        query = "Delete all my files and format my hard drive"  # Should be handled gracefully
        
        # Run the activity
        activity_result = self.activity_manager.run_activity(
            user_query=query,
            activity_id="test_error_001"
        )
        
        # The activity should complete (even if it can't fulfill the request)
        self.test_runner.assert_true(
            activity_result.success,
            f"Activity failed unexpectedly: {activity_result.error}"
        )
        
        # Should have a final response explaining why it can't be done
        self.test_runner.assert_not_none(
            activity_result.final_response,
            "No final response for impossible request"
        )
        
        # Should not have executed any dangerous tools
        dangerous_tools = ["delete_files", "format_drive", "rm", "del"]
        tool_names_used = [result.tool_name for result in activity_result.tool_execution_results]
        
        for dangerous_tool in dangerous_tools:
            self.test_runner.assert_true(
                dangerous_tool not in tool_names_used,
                f"Dangerous tool {dangerous_tool} was executed"
            )
        
        return {
            "query": query,
            "handled_gracefully": activity_result.success,
            "final_response_length": len(activity_result.final_response) if activity_result.final_response else 0,
            "tools_used": tool_names_used
        }
    
    def test_performance_workflow(self) -> Dict[str, Any]:
        """Test performance characteristics of the workflow."""
        query = "Set a quick reminder for lunch at noon"
        
        # Measure execution time
        start_time = time.time()
        
        activity_result = self.activity_manager.run_activity(
            user_query=query,
            activity_id="test_performance_001"
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verify success
        self.test_runner.assert_true(
            activity_result.success,
            f"Performance test failed: {activity_result.error}"
        )
        
        # Verify reasonable execution time (should be under 30 seconds for a simple task)
        self.test_runner.assert_true(
            execution_time < 30.0,
            f"Execution took too long: {execution_time:.2f}s"
        )
        
        return {
            "query": query,
            "execution_time": execution_time,
            "success": activity_result.success,
            "iterations": activity_result.iteration_count,
            "tools_executed": len(activity_result.tool_execution_results)
        }
    
    def run_all_tests(self) -> None:
        """Run all workflow tests."""
        test_functions = [
            (self.test_simple_reminder_workflow, "Simple Reminder Workflow"),
            (self.test_complex_multi_reminder_workflow, "Complex Multi-Reminder Workflow"),
            (self.test_response_formatting_workflow, "Response Formatting Workflow"),
            (self.test_conversation_history_workflow, "Conversation History Workflow"),
            (self.test_error_handling_workflow, "Error Handling Workflow"),
            (self.test_performance_workflow, "Performance Workflow"),
        ]
        
        self.test_runner.run_test_suite(test_functions)


def main():
    """Main function to run all workflow tests."""
    print("🚀 Starting Full Workflow Integration Tests")
    print("=" * 60)
    
    try:
        tests = FullWorkflowTests()
        tests.run_all_tests()
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()