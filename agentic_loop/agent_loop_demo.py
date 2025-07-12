"""
Agent Loop Demo - Demonstration of the agentic loop architecture with tool sets.

This demo showcases the agentic loop's ability to:
1. Load different tool sets (treasure_hunt, productivity, ecommerce)
2. Execute multi-tool selections through iterations
3. Track reasoning and tool execution across loops
4. Evaluate performance with detailed metrics
"""

import sys
import os
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import shared utilities
from shared_utils import (
    ToolSelectionMetrics,
    TestResult,
    TestSummary,
    ToolSelectionEvaluation,
    ConsoleFormatter,
    setup_llm
)

# Import agentic loop components
from agentic_loop.manual_agent_loop import ManualAgentLoop
from agentic_loop.activity_manager import ActivityManager

# Import shared models
from shared.models import ToolCall
from shared.tool_set_registry import ToolSetRegistry

# Import tool sets
from tool_selection.tool_sets import (
    TreasureHuntToolSet,
    ProductivityToolSet,
    EcommerceToolSet,
    ToolSetTestCase
)


def create_tool_set_registry(tool_set_name: str) -> ToolSetRegistry:
    """
    Create and populate a tool set registry with the specified tool set.
    
    Args:
        tool_set_name: Name of the tool set to load
        
    Returns:
        ToolSetRegistry configured with the requested tool set
    """
    registry = ToolSetRegistry()
    
    # Map tool set names to their classes
    tool_set_map = {
        "treasure_hunt": TreasureHuntToolSet,
        "productivity": ProductivityToolSet,
        "ecommerce": EcommerceToolSet
    }
    
    # Get the tool set class
    tool_set_class = tool_set_map.get(tool_set_name)
    if not tool_set_class:
        raise ValueError(f"Unknown tool set: {tool_set_name}. Available: {list(tool_set_map.keys())}")
    
    # Create tool set instance
    tool_set = tool_set_class()
    
    # Register the tool set
    registry.register_tool_set(
        tool_set_name=tool_set_name,
        description=tool_set.config.description,
        tool_classes=tool_set.config.tool_classes
    )
    
    return registry


def run_agent_loop_demo(tool_set_name: str = "productivity", use_advanced: bool = False) -> Dict[str, Any]:
    """
    Run the agent loop demo with the specified tool set.
    
    Args:
        tool_set_name: Name of the tool set to use
        use_advanced: Whether to use advanced reasoning capabilities
        
    Returns:
        Dictionary containing summary and detailed results
    """
    start_time = time.time()
    formatter = ConsoleFormatter()
    metrics = ToolSelectionMetrics()
    
    mode_str = "Advanced" if use_advanced else "Basic"
    print(formatter.section_header(f"🚀 Agent Loop Demo - {mode_str} Agentic Architecture"))
    print(f"Testing agentic loop with multi-tool selection capabilities")
    print(f"Tool Set: {tool_set_name}")
    print(f"Mode: {mode_str}\n")
    
    # Setup LLM
    try:
        setup_llm()
    except Exception as e:
        print(formatter.error_message(f"Failed to setup LLM: {e}"))
        return {"error": f"Failed to setup LLM: {e}"}
    
    # Create tool registry and load tool set
    print(f"Loading tool set: {tool_set_name}")
    try:
        tool_registry = create_tool_set_registry(tool_set_name)
        tool_names = tool_registry.get_tool_names()
        print(f"Loaded {len(tool_names)} tools: {tool_names}\n")
    except ValueError as e:
        print(formatter.error_message(str(e)))
        return {"error": str(e)}
    
    # Create agent loop and activity manager
    # Use environment variables for configuration with sensible defaults
    max_iterations = int(os.getenv('AGENT_MAX_ITERATIONS', '5'))
    timeout_seconds = float(os.getenv('AGENT_TIMEOUT_SECONDS', '60.0'))
    
    # Check if advanced mode is requested via env var
    if os.getenv('AGENT_USE_ADVANCED', '').lower() == 'true':
        use_advanced = True
    
    if use_advanced:
        # Use advanced agent loop with enhanced reasoning
        from agentic_loop.advanced import AdvancedManualAgentLoop
        
        # Create advanced agent loop
        agent_loop = AdvancedManualAgentLoop(
            tool_names=tool_names,
            max_iterations=max_iterations
        )
        print(f"Using Advanced Agent Loop with enhanced capabilities:")
        print(f"  - Tool result analysis")
        print(f"  - Goal tracking and progress monitoring") 
        print(f"  - Dynamic strategy adaptation")
        print(f"  - Enhanced error recovery\n")
    else:
        agent_loop = ManualAgentLoop(
            tool_names=tool_names,
            max_iterations=max_iterations  # Allow multiple iterations for complex tasks
        )
    
    activity_manager = ActivityManager(
        agent_loop=agent_loop,
        tool_registry=tool_registry,
        max_iterations=max_iterations,
        timeout_seconds=timeout_seconds
    )
    
    # Get test cases for the tool set
    tool_set_class = {
        "treasure_hunt": TreasureHuntToolSet,
        "productivity": ProductivityToolSet,
        "ecommerce": EcommerceToolSet
    }[tool_set_name]
    
    test_cases = tool_set_class.get_test_cases()
    print(f"Running {len(test_cases)} test cases\n")
    
    # Track results
    test_results = []
    evaluations = []
    
    print(formatter.section_separator())
    
    for i, test_case in enumerate(test_cases, 1):
        test_start = time.time()
        
        print(formatter.test_progress(i, len(test_cases), test_case.description))
        print(f"👤 User: {test_case.request}")
        print(f"🎯 Expected tools: {test_case.expected_tools}")
        
        try:
            # Run the activity through the agent loop
            activity_result = activity_manager.run_activity(
                user_query=test_case.request,
                activity_id=f"test_{i:03d}"
            )
            
            # Extract tools used from activity result
            actual_tools = activity_result.tools_used
            
            print(f"\n🤖 Selected tools: {actual_tools}")
            print(f"   Status: {activity_result.status}")
            print(f"   Iterations: {activity_result.total_iterations}")
            
            # Show reasoning from conversation state
            if activity_result.conversation_state.conversation_history:
                for i, entry in enumerate(activity_result.conversation_state.conversation_history, 1):
                    if hasattr(entry, 'reasoning') and entry.reasoning:
                        print(f"   Iteration {i} reasoning: {entry.reasoning[:100]}...")
            
            # Evaluate selection
            expected_set = set(test_case.expected_tools)
            actual_set = set(actual_tools)
            evaluation = metrics.evaluate_selection(expected_set, actual_set)
            
            # Create evaluation object
            eval_obj = ToolSelectionEvaluation(**evaluation)
            
            print(f"\n📊 Evaluation:")
            comparison_lines = formatter.format_tool_comparison(
                test_case.expected_tools,
                actual_tools
            )
            for line in comparison_lines:
                print(f"   {line}")
            
            metric_lines = formatter.format_metrics_summary(evaluation)
            for line in metric_lines:
                print(f"   {line}")
            
            # Show execution results from conversation state
            if activity_result.conversation_state.last_tool_results:
                print(f"\n🔧 Execution results:")
                for tool_result in activity_result.conversation_state.last_tool_results:
                    if tool_result.success:
                        success_msg = f"{tool_result.tool_name}: {tool_result.result}"
                        print(f"   {formatter.success_message(success_msg)}")
                    else:
                        error_msg = f"{tool_result.tool_name}: {tool_result.error}"
                        print(f"   {formatter.error_message(error_msg)}")
            
            # Create test result
            test_result = TestResult(
                test_case=test_case,
                actual_tools=actual_tools,
                reasoning=activity_result.final_response or "",
                evaluation=eval_obj,
                execution_results=[{
                    "tool": tr.tool_name,
                    "result": tr.result if tr.success else tr.error,
                    "success": tr.success
                } for tr in activity_result.conversation_state.last_tool_results] if activity_result.conversation_state.last_tool_results else None,
                error=None if activity_result.status == "completed" else f"Activity status: {activity_result.status}",
                duration_ms=(time.time() - test_start) * 1000
            )
            
            test_results.append(test_result)
            evaluations.append(evaluation)
            
        except Exception as e:
            # Handle errors
            error_result = TestResult(
                test_case=test_case,
                actual_tools=[],
                reasoning="",
                evaluation=ToolSelectionEvaluation(
                    precision=0.0,
                    recall=0.0,
                    f1_score=0.0,
                    is_perfect_match=False
                ),
                error=str(e),
                duration_ms=(time.time() - test_start) * 1000
            )
            test_results.append(error_result)
            
            error_msg = f'Error: {e}'
            print(f"   {formatter.error_message(error_msg)}")
        
        print(f"\n{formatter.section_separator()}\n")
    
    # Calculate summary statistics
    aggregate_metrics = metrics.aggregate_metrics(evaluations)
    
    # Create summary
    summary = TestSummary(
        model=os.getenv("OLLAMA_MODEL", "unknown"),
        total_tests=len(test_cases),
        passed_tests=sum(1 for r in test_results if r.error is None),
        perfect_matches=aggregate_metrics["perfect_matches"],
        avg_precision=aggregate_metrics["avg_precision"],
        avg_recall=aggregate_metrics["avg_recall"],
        avg_f1_score=aggregate_metrics["avg_f1_score"],
        total_duration_seconds=time.time() - start_time
    )
    
    # Print summary
    summary_data = {
        "Tool Set": tool_set_name,
        "Total tests": summary.total_tests,
        "Passed tests": summary.passed_tests,
        "Perfect matches": f"{summary.perfect_matches}/{summary.total_tests} ({summary.perfect_match_rate:.1f}%)",
        "Average precision": summary.avg_precision,
        "Average recall": summary.avg_recall,
        "Average F1 score": summary.avg_f1_score,
        "Success rate": f"{summary.success_rate:.1f}%",
        "Total duration": f"{summary.total_duration_seconds:.2f}s"
    }
    
    print(formatter.format_summary_table(
        summary_data,
        title="📊 AGENT LOOP PERFORMANCE SUMMARY"
    ))
    
    # Show performance bars
    print("\nPerformance Visualization:")
    print(f"Precision: {formatter.performance_bar(summary.avg_precision)}")
    print(f"Recall:    {formatter.performance_bar(summary.avg_recall)}")
    print(f"F1 Score:  {formatter.performance_bar(summary.avg_f1_score)}")
    
    # Show loaded tools
    print(f"\n📦 Tool Set: {tool_set_name}")
    print(f"   Tools: {tool_names}")
    
    print(formatter.success_message("\n✅ Agent loop demo complete!"))
    
    # Include calculated properties in the summary dict
    summary_dict = summary.model_dump()
    summary_dict['success_rate'] = summary.success_rate
    summary_dict['perfect_match_rate'] = summary.perfect_match_rate
    
    return {
        "tool_set": tool_set_name,
        "summary": summary_dict,
        "detailed_results": [r.model_dump() for r in test_results],
        "model": summary.model,
        "timestamp": summary.timestamp.isoformat()
    }


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Run agent loop demo with specified tool set"
    )
    parser.add_argument(
        "tool_set",
        nargs="?",
        default="productivity",
        choices=["treasure_hunt", "productivity", "ecommerce"],
        help="Tool set to load (default: productivity)"
    )
    parser.add_argument(
        "--advanced",
        action="store_true",
        help="Use advanced agentic loop with enhanced reasoning capabilities"
    )
    
    args = parser.parse_args()
    
    # Run the demo
    results = run_agent_loop_demo(args.tool_set, use_advanced=args.advanced)
    
    # Save results to JSON
    if 'error' not in results:
        # Create test_results directory if it doesn't exist
        results_dir = Path("test_results")
        results_dir.mkdir(exist_ok=True)
        
        # Create filename with tool set name and timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = results_dir / f"agent_loop_{args.tool_set}_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    main()