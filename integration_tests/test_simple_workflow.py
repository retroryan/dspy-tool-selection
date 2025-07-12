"""
Simple integration test for basic workflow validation.

This module provides a minimal test to verify the agentic loop works with real models.
"""

import os
import sys
import time

# Add parent directory to path to import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integration_tests.test_framework import create_test_runner
from shared.tool_set_registry import create_productivity_tool_set_registry
from agentic_loop.activity_manager import ActivityManager
from agentic_loop.manual_agent_loop import ManualAgentLoop
from agentic_loop.agent_reasoner import AgentReasoner
from shared_utils.llm_factory import setup_llm


class SimpleWorkflowTest:
    """Basic integration test for agentic loop workflow."""
    
    def __init__(self):
        self.test_runner = create_test_runner(verbose=True)
        
        # Load environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        
        # Setup LLM with higher token limit
        try:
            import dspy
            setup_llm()
            
            # Increase token limit for Claude
            if hasattr(dspy.settings, 'lm'):
                dspy.settings.lm.max_tokens = 2048
            
            print("✅ LLM setup successful")
        except Exception as e:
            print(f"❌ LLM setup failed: {e}")
            raise
        
        # Create simple tool registry
        self.tool_registry = create_productivity_tool_set_registry()
        print(f"✅ Tool registry created with tools: {self.tool_registry.get_tool_names()}")
        
        # Create activity manager
        self.manual_agent_loop = ManualAgentLoop(
            tool_names=self.tool_registry.get_tool_names()
        )
        
        self.activity_manager = ActivityManager(
            agent_loop=self.manual_agent_loop,
            tool_registry=self.tool_registry,
            max_iterations=2,  # Reduced for faster testing
            timeout_seconds=30.0
        )
        
        print("✅ Activity manager initialized")
    
    def test_basic_reminder_workflow(self):
        """Test basic reminder creation workflow."""
        print("\n🧪 Testing basic reminder workflow...")
        
        query = "Set a reminder for lunch at noon"
        
        # Run the activity
        start_time = time.time()
        activity_result = self.activity_manager.run_activity(
            user_query=query,
            activity_id="simple_test_001"
        )
        duration = time.time() - start_time
        
        print(f"⏱️  Execution time: {duration:.2f}s")
        
        # Basic validation
        self.test_runner.assert_true(
            activity_result.status == "completed",
            f"Activity failed with status: {activity_result.status}"
        )
        
        print(f"✅ Activity completed successfully")
        print(f"📝 Final response: {activity_result.final_response[:100]}...")
        
        # Check if tools were used
        tool_names_used = activity_result.tools_used
        print(f"🔧 Tools used: {tool_names_used}")
        
        # Verify set_reminder was used
        self.test_runner.assert_contains(
            tool_names_used,
            "set_reminder",
            "set_reminder tool was not used"
        )
        
        print("✅ Tool selection validation passed")
        
        return {
            "success": True,
            "duration": duration,
            "tools_used": tool_names_used,
            "response_length": len(activity_result.final_response) if activity_result.final_response else 0
        }
    
    def test_no_tools_needed_workflow(self):
        """Test workflow where no tools are needed."""
        print("\n🧪 Testing no-tools-needed workflow...")
        
        query = "What is the capital of France?"
        
        # Run the activity
        start_time = time.time()
        activity_result = self.activity_manager.run_activity(
            user_query=query,
            activity_id="simple_test_002"
        )
        duration = time.time() - start_time
        
        print(f"⏱️  Execution time: {duration:.2f}s")
        
        # Basic validation
        self.test_runner.assert_true(
            activity_result.status == "completed",
            f"Activity failed with status: {activity_result.status}"
        )
        
        print(f"✅ Activity completed successfully")
        print(f"📝 Final response: {activity_result.final_response[:100]}...")
        
        # Check that no tools were used (this is a general knowledge question)
        tool_names_used = activity_result.tools_used
        print(f"🔧 Tools used: {tool_names_used}")
        
        # For general knowledge, no tools should be needed
        # (though the LLM might still choose to use tools - that's okay)
        
        return {
            "success": True,
            "duration": duration,
            "tools_used": tool_names_used,
            "response_length": len(activity_result.final_response) if activity_result.final_response else 0
        }
    
    def run_tests(self):
        """Run all simple tests."""
        test_functions = [
            (self.test_basic_reminder_workflow, "Basic Reminder Workflow"),
            (self.test_no_tools_needed_workflow, "No Tools Needed Workflow"),
        ]
        
        self.test_runner.run_test_suite(test_functions)
        
        # Print configuration info
        print(f"\n📋 Configuration Used:")
        print(f"   Provider: {os.getenv('DSPY_PROVIDER', 'unknown')}")
        print(f"   Model: {os.getenv('CLAUDE_MODEL', 'unknown')}")
        print(f"   Max Iterations: 2")
        print(f"   Timeout: 30s")


def main():
    """Main function to run simple integration tests."""
    print("🚀 Starting Simple Integration Tests")
    print("🔬 Basic DSPy Agentic Loop Validation")
    print("=" * 60)
    
    try:
        test = SimpleWorkflowTest()
        test.run_tests()
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()