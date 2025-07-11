"""Multi-tool DSPy selection demo using the new centralized registry.

This demo tests the model's ability to:
1. Select the correct tool from many options
2. Handle ambiguous requests
3. Select multiple tools when needed
4. Extract proper arguments
"""

import sys
from pathlib import Path
import os
import json
from datetime import datetime
from typing import Dict, List, Set, Any
import time

sys.path.append(str(Path(__file__).parent.parent))

# Import new registry and models
from .registry import registry
from .base_tool import BaseTool, ToolTestCase
from .tool_sets import tool_set_registry, TreasureHuntToolSet, ProductivityToolSet

# Import shared utilities
from shared_utils.llm_factory import setup_llm
import dspy
from pydantic import BaseModel, Field

# Import shared utilities
from shared_utils import (
    ToolSelectionMetrics, 
    TestCase, 
    TestResult, 
    TestSummary,
    ToolSelectionEvaluation,
    ConsoleFormatter
)

# Import the updated selector
from .multi_tool_selector import MultiToolSelector
from .models import MultiToolDecision, ToolCall


def load_tools_from_sets(tool_set_names: List[str] = None):
    """Load tools from specified tool sets.
    
    Args:
        tool_set_names: List of tool set names to load. If None, loads all.
    """
    if tool_set_names is None:
        # Load all available tool sets
        for name, tool_set in tool_set_registry.get_all_tool_sets().items():
            tool_set.load()
    else:
        # Load specific tool sets
        for name in tool_set_names:
            tool_set_registry.load_tool_set(name)


def get_test_cases_from_registry() -> List[TestCase]:
    """Get test cases from all registered tools and tool sets."""
    test_cases = []
    
    # Get test cases from individual tools
    tool_test_cases = registry.get_all_test_cases()
    
    # Get test cases from tool sets
    tool_set_test_cases = tool_set_registry.get_all_test_cases()
    
    # Convert to shared TestCase format
    for tc in tool_test_cases + tool_set_test_cases:
        test_cases.append(TestCase(
            request=tc.request,
            expected_tools=tc.expected_tools,
            description=tc.description
        ))
    
    return test_cases


def convert_tools_to_definitions() -> List['MultiTool']:
    """Convert registered tools to the format expected by MultiToolSelector."""
    from .models import MultiTool, MultiToolName, ToolArgument
    
    definitions = []
    for tool in registry.get_all_tools().values():
        schema = tool.to_schema()
        
        # Convert tool name to enum
        try:
            tool_name_enum = MultiToolName(schema['name'])
        except ValueError:
            # Skip tools not in the MultiToolName enum
            continue
            
        # Convert arguments to ToolArgument format
        tool_arguments = []
        for arg in schema['arguments']:
            tool_arguments.append(ToolArgument(
                name=arg['name'],
                type=arg['type'],
                description=arg['description']
            ))
        
        multi_tool = MultiTool(
            name=tool_name_enum,
            description=schema['description'],
            arguments=tool_arguments,
            category=tool.metadata.category
        )
        definitions.append(multi_tool)
    
    return definitions


def execute_decision(decision: MultiToolDecision) -> List[dict]:
    """Execute tools based on the decision using the new registry."""
    results = []
    
    for tool_call in decision.tool_calls:
        try:
            # Execute using the new registry
            result = registry.execute_tool(
                tool_call.tool_name,
                **tool_call.arguments
            )
            results.append({
                "tool": tool_call.tool_name,
                "result": result
            })
        except ValueError as e:
            results.append({
                "tool": tool_call.tool_name,
                "error": str(e)
            })
        except Exception as e:
            results.append({
                "tool": tool_call.tool_name,
                "error": f"Execution error: {str(e)}"
            })
    
    return results


def run_demo(predict=False, tool_sets=None):
    """Run the multi-tool demo using the new registry.
    
    Args:
        predict: If True, use dspy.Predict instead of dspy.ChainOfThought
        tool_sets: List of tool set names to load. If None, loads default sets.
        
    Returns:
        Dictionary containing summary and detailed results
    """
    start_time = time.time()
    formatter = ConsoleFormatter()
    metrics = ToolSelectionMetrics()
    
    print(formatter.section_header("🚀 DSPy Multi-Tool Selection Demo (New Registry)"))
    print("Testing LLM's capacity for multi-tool selection using centralized registry")
    print(f"Mode: {'dspy.Predict' if predict else 'dspy.ChainOfThought'}\n")
    
    # Setup LLM
    try:
        setup_llm()
    except Exception as e:
        print(formatter.error_message(f"Failed to setup Ollama: {e}"))
        return {"error": f"Failed to setup Ollama: {e}"}
    
    # Load tools from tool sets
    if tool_sets is None:
        # Default to loading productivity set
        tool_sets = [ProductivityToolSet.NAME]
    
    print(f"Loading tool sets: {tool_sets}")
    
    load_tools_from_sets(tool_sets)
    
    # Get tool definitions and test cases
    tool_definitions = convert_tools_to_definitions()
    test_cases = get_test_cases_from_registry()
    
    print(f"Loaded {len(tool_definitions)} tools with {len(test_cases)} test cases\n")
    
    # Initialize selector with dynamic tool names
    selector = MultiToolSelector(use_predict=predict)
    
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
            # Get LLM's decision
            decision = selector(test_case.request, tool_definitions)
            
            # Extract actual tools selected
            actual_tools = [tc.tool_name for tc in decision.tool_calls]
            
            print(f"\n🤖 Selected tools: {actual_tools}")
            print(f"   Reasoning: {decision.reasoning}")
            
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
            
            # Execute tools and collect results
            execution_results = []
            execution_error = None
            
            try:
                results = execute_decision(decision)
                execution_results = results
                
                print(f"\n🔧 Execution results:")
                for result in results:
                    if 'error' in result:
                        error_msg = f"{result['tool']}: {result['error']}"
                        print(f"   {formatter.error_message(error_msg)}")
                    else:
                        success_msg = f"{result['tool']}: {result['result']}"
                        print(f"   {formatter.success_message(success_msg)}")
            except Exception as e:
                execution_error = str(e)
                error_msg = f'Execution error: {e}'
                print(f"   {formatter.error_message(error_msg)}")
            
            # Create test result
            test_result = TestResult(
                test_case=test_case,
                actual_tools=actual_tools,
                reasoning=decision.reasoning,
                evaluation=eval_obj,
                execution_results=execution_results if execution_results else None,
                error=execution_error,
                duration_ms=(time.time() - test_start) * 1000
            )
            
            test_results.append(test_result)
            evaluations.append(evaluation)
                
        except Exception as e:
            # Handle selection error
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
            
            error_msg = f'Selection error: {e}'
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
        title="📊 OVERALL PERFORMANCE SUMMARY"
    ))
    
    # Show performance bars
    print("\nPerformance Visualization:")
    print(f"Precision: {formatter.performance_bar(summary.avg_precision)}")
    print(f"Recall:    {formatter.performance_bar(summary.avg_recall)}")
    print(f"F1 Score:  {formatter.performance_bar(summary.avg_f1_score)}")
    
    # Show loaded tools
    print(f"\n📦 Loaded Tools ({len(registry.get_all_tools())}): {list(registry.get_tool_names())}")
    
    print(formatter.success_message("\n✅ Multi-tool demo complete!"))
    
    return {
        "summary": summary.model_dump(),
        "detailed_results": [r.model_dump() for r in test_results],
        "model": summary.model,
        "timestamp": summary.timestamp.isoformat()
    }


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run multi-tool selection demo with new registry")
    parser.add_argument("tool_set", nargs="?", default=ProductivityToolSet.NAME,
                        help=f"Tool set to load (default: {ProductivityToolSet.NAME})")
    parser.add_argument("--predict", action="store_true", 
                        help="Use dspy.Predict instead of dspy.ChainOfThought")
    parser.add_argument("--tool-sets", nargs="+", 
                        help="Tool sets to load (overrides positional argument)")
    
    args = parser.parse_args()
    
    # Determine which tool sets to use
    if args.tool_sets:
        tool_sets = args.tool_sets
    else:
        tool_sets = [args.tool_set]
    
    results = run_demo(
        predict=args.predict,
        tool_sets=tool_sets
    )
    
    # Save to file
    if 'error' not in results:
        with open('test_results_new.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: test_results_new.json")


if __name__ == "__main__":
    main()