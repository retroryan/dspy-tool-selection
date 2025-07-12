"""
Real model and tools integration tests.

This module tests the agentic loop with actual LLM models and various tool sets
to ensure everything works together in practice.
"""

import os
import sys
import time
from typing import List, Dict, Any, Optional

# Add parent directory to path to import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integration_tests.test_framework import create_test_runner
from shared.tool_set_registry import (
    create_productivity_tool_set_registry,
    create_tool_set_registry,
    create_ecommerce_tool_set_registry
)
from agentic_loop.activity_manager import ActivityManager
from agentic_loop.manual_agent_loop import ManualAgentLoop
from agentic_loop.agent_reasoner import AgentReasoner
from shared.models import ConversationState
from shared_utils.llm_factory import setup_llm
from tool_selection.tool_sets import ProductivityToolSet, TreasureHuntToolSet, EcommerceToolSet


class RealModelToolTests:
    """Integration tests with real LLM models and various tool sets."""
    
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
        
        # Initialize different tool registries
        self.productivity_registry = create_productivity_tool_set_registry()
        self.treasure_hunt_registry = create_tool_set_registry()
        self.ecommerce_registry = create_ecommerce_tool_set_registry()
        
        print("✅ All tool registries initialized")
    
    def create_activity_manager(self, tool_registry) -> ActivityManager:
        """Create an activity manager with the given tool registry."""
        agent_reasoner = AgentReasoner(
            tool_names=tool_registry.get_tool_names(),
            max_iterations=3
        )
        
        manual_agent_loop = ManualAgentLoop(
            tool_names=tool_registry.get_tool_names()
        )
        
        return ActivityManager(
            agent_loop=manual_agent_loop,
            tool_registry=tool_registry,
            max_iterations=3,
            timeout_seconds=45.0
        )
    
    def test_productivity_tools_with_real_model(self) -> Dict[str, Any]:
        """Test productivity tools with real LLM model."""
        activity_manager = self.create_activity_manager(self.productivity_registry)
        
        # Test different productivity scenarios
        test_cases = [
            "Set a reminder for my team meeting tomorrow at 10 AM",
            "Remind me to call my mom on Sunday at 2 PM",
            "Create a reminder for the project deadline next Friday at 9 AM"
        ]
        
        results = {}
        
        for i, query in enumerate(test_cases):
            activity_result = activity_manager.run_activity(
                user_query=query,
                activity_id=f"productivity_test_{i+1}"
            )
            
            # Verify success
            self.test_runner.assert_true(
                activity_result.success,
                f"Productivity test {i+1} failed: {activity_result.error}"
            )
            
            # Verify set_reminder was used
            tool_names_used = [result.tool_name for result in activity_result.tool_execution_results]
            self.test_runner.assert_contains(
                tool_names_used,
                "set_reminder",
                f"set_reminder not used in test case {i+1}"
            )
            
            results[f"case_{i+1}"] = {
                "query": query,
                "success": activity_result.success,
                "tools_used": tool_names_used,
                "iterations": activity_result.iteration_count
            }
        
        return {
            "total_cases": len(test_cases),
            "all_successful": all(result["success"] for result in results.values()),
            "results": results
        }
    
    def test_treasure_hunt_tools_with_real_model(self) -> Dict[str, Any]:
        """Test treasure hunt tools with real LLM model."""
        activity_manager = self.create_activity_manager(self.treasure_hunt_registry)
        
        # Test treasure hunt scenarios
        test_cases = [
            "I need help finding the treasure",
            "Give me a hint about where the treasure might be",
            "I think the treasure is at the library"
        ]
        
        results = {}
        
        for i, query in enumerate(test_cases):
            activity_result = activity_manager.run_activity(
                user_query=query,
                activity_id=f"treasure_hunt_test_{i+1}"
            )
            
            # Verify success
            self.test_runner.assert_true(
                activity_result.success,
                f"Treasure hunt test {i+1} failed: {activity_result.error}"
            )
            
            # Verify appropriate tools were used
            tool_names_used = [result.tool_name for result in activity_result.tool_execution_results]
            expected_tools = ["give_hint", "guess_location"]
            
            # At least one of the expected tools should be used
            used_expected_tool = any(tool in tool_names_used for tool in expected_tools)
            self.test_runner.assert_true(
                used_expected_tool,
                f"No expected tools used in test case {i+1}. Used: {tool_names_used}"
            )
            
            results[f"case_{i+1}"] = {
                "query": query,
                "success": activity_result.success,
                "tools_used": tool_names_used,
                "iterations": activity_result.iteration_count
            }
        
        return {
            "total_cases": len(test_cases),
            "all_successful": all(result["success"] for result in results.values()),
            "results": results
        }
    
    def test_ecommerce_tools_with_real_model(self) -> Dict[str, Any]:
        """Test ecommerce tools with real LLM model."""
        activity_manager = self.create_activity_manager(self.ecommerce_registry)
        
        # Test ecommerce scenarios
        test_cases = [
            "Search for wireless headphones under $100",
            "Check the status of my order 12345",
            "I want to return item ABC123 because it's defective"
        ]
        
        results = {}
        
        for i, query in enumerate(test_cases):
            activity_result = activity_manager.run_activity(
                user_query=query,
                activity_id=f"ecommerce_test_{i+1}"
            )
            
            # Verify success
            self.test_runner.assert_true(
                activity_result.success,
                f"Ecommerce test {i+1} failed: {activity_result.error}"
            )
            
            # Verify appropriate tools were used
            tool_names_used = [result.tool_name for result in activity_result.tool_execution_results]
            
            # Different queries should use different tools
            expected_tools_by_case = [
                ["search_products"],  # Search query
                ["track_order", "get_order"],  # Order status
                ["return_item"]  # Return request
            ]
            
            expected_tools = expected_tools_by_case[i]
            used_expected_tool = any(tool in tool_names_used for tool in expected_tools)
            
            self.test_runner.assert_true(
                used_expected_tool,
                f"No expected tools used in test case {i+1}. Expected: {expected_tools}, Used: {tool_names_used}"
            )
            
            results[f"case_{i+1}"] = {
                "query": query,
                "success": activity_result.success,
                "tools_used": tool_names_used,
                "expected_tools": expected_tools,
                "iterations": activity_result.iteration_count
            }
        
        return {
            "total_cases": len(test_cases),
            "all_successful": all(result["success"] for result in results.values()),
            "results": results
        }
    
    def test_model_reasoning_quality(self) -> Dict[str, Any]:
        """Test the quality of model reasoning with complex queries."""
        activity_manager = self.create_activity_manager(self.productivity_registry)
        
        # Complex query that requires reasoning
        complex_query = (
            "I have a busy day tomorrow. I need to wake up early for a 7 AM workout, "
            "then I have a client meeting at 9 AM, lunch with my team at 12:30 PM, "
            "and I need to finish my project report by 5 PM. "
            "Can you help me set up reminders for these important events?"
        )
        
        activity_result = activity_manager.run_activity(
            user_query=complex_query,
            activity_id="reasoning_quality_test"
        )
        
        # Verify success
        self.test_runner.assert_true(
            activity_result.success,
            f"Complex reasoning test failed: {activity_result.error}"
        )
        
        # Verify tools were used
        self.test_runner.assert_greater_than(
            len(activity_result.tool_execution_results),
            0,
            "No tools were executed for complex query"
        )
        
        # Verify set_reminder was used
        tool_names_used = [result.tool_name for result in activity_result.tool_execution_results]
        self.test_runner.assert_contains(
            tool_names_used,
            "set_reminder",
            "set_reminder not used for complex scheduling query"
        )
        
        # Verify the response is comprehensive
        response_length = len(activity_result.final_response) if activity_result.final_response else 0
        self.test_runner.assert_greater_than(
            response_length,
            50,
            "Response too short for complex query"
        )
        
        return {
            "query": complex_query,
            "success": activity_result.success,
            "tools_used": tool_names_used,
            "tool_execution_count": len(activity_result.tool_execution_results),
            "response_length": response_length,
            "iterations": activity_result.iteration_count
        }
    
    def test_tool_selection_accuracy(self) -> Dict[str, Any]:
        """Test accuracy of tool selection for different query types."""
        
        # Test with different tool sets and targeted queries
        test_scenarios = [
            {
                "registry": self.productivity_registry,
                "query": "Set a reminder for my dentist appointment",
                "expected_tools": ["set_reminder"],
                "name": "productivity_targeted"
            },
            {
                "registry": self.treasure_hunt_registry,
                "query": "I need a hint to find the treasure",
                "expected_tools": ["give_hint"],
                "name": "treasure_hunt_targeted"
            },
            {
                "registry": self.ecommerce_registry,
                "query": "Search for running shoes",
                "expected_tools": ["search_products"],
                "name": "ecommerce_targeted"
            }
        ]
        
        results = {}
        
        for scenario in test_scenarios:
            activity_manager = self.create_activity_manager(scenario["registry"])
            
            activity_result = activity_manager.run_activity(
                user_query=scenario["query"],
                activity_id=f"tool_selection_{scenario['name']}"
            )
            
            # Verify success
            self.test_runner.assert_true(
                activity_result.success,
                f"Tool selection test {scenario['name']} failed: {activity_result.error}"
            )
            
            # Verify correct tools were selected
            tool_names_used = [result.tool_name for result in activity_result.tool_execution_results]
            
            # Check if any of the expected tools were used
            correct_tool_used = any(tool in tool_names_used for tool in scenario["expected_tools"])
            
            self.test_runner.assert_true(
                correct_tool_used,
                f"Incorrect tool selection for {scenario['name']}. Expected: {scenario['expected_tools']}, Used: {tool_names_used}"
            )
            
            results[scenario["name"]] = {
                "query": scenario["query"],
                "expected_tools": scenario["expected_tools"],
                "tools_used": tool_names_used,
                "correct_selection": correct_tool_used,
                "success": activity_result.success
            }
        
        all_correct = all(result["correct_selection"] for result in results.values())
        
        return {
            "total_scenarios": len(test_scenarios),
            "all_correct_selections": all_correct,
            "results": results
        }
    
    def test_model_configuration_validation(self) -> Dict[str, Any]:
        """Test that the model configuration is working correctly."""
        activity_manager = self.create_activity_manager(self.productivity_registry)
        
        # Simple test to validate model is responding
        simple_query = "Set a reminder for lunch at noon"
        
        start_time = time.time()
        activity_result = activity_manager.run_activity(
            user_query=simple_query,
            activity_id="model_config_test"
        )
        execution_time = time.time() - start_time
        
        # Verify success
        self.test_runner.assert_true(
            activity_result.success,
            f"Model configuration test failed: {activity_result.error}"
        )
        
        # Verify we got a response
        self.test_runner.assert_not_none(
            activity_result.final_response,
            "No response from model"
        )
        
        # Verify execution time is reasonable
        self.test_runner.assert_true(
            execution_time < 60.0,
            f"Model response too slow: {execution_time:.2f}s"
        )
        
        return {
            "model_responding": activity_result.success,
            "execution_time": execution_time,
            "response_length": len(activity_result.final_response) if activity_result.final_response else 0,
            "tools_executed": len(activity_result.tool_execution_results)
        }
    
    def run_all_tests(self) -> None:
        """Run all real model and tool tests."""
        test_functions = [
            (self.test_model_configuration_validation, "Model Configuration Validation"),
            (self.test_productivity_tools_with_real_model, "Productivity Tools with Real Model"),
            (self.test_treasure_hunt_tools_with_real_model, "Treasure Hunt Tools with Real Model"),
            (self.test_ecommerce_tools_with_real_model, "Ecommerce Tools with Real Model"),
            (self.test_model_reasoning_quality, "Model Reasoning Quality"),
            (self.test_tool_selection_accuracy, "Tool Selection Accuracy"),
        ]
        
        self.test_runner.run_test_suite(test_functions)


def main():
    """Main function to run all real model and tool tests."""
    print("🤖 Starting Real Model and Tools Integration Tests")
    print("=" * 60)
    
    # Check environment configuration
    provider = os.getenv("DSPY_PROVIDER", "unknown")
    model = os.getenv("OLLAMA_MODEL", "unknown") if provider == "ollama" else os.getenv("CLAUDE_MODEL", "unknown")
    
    print(f"📋 Configuration:")
    print(f"   Provider: {provider}")
    print(f"   Model: {model}")
    print("=" * 60)
    
    try:
        tests = RealModelToolTests()
        tests.run_all_tests()
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()