"""Multi-tool DSPy selection demo to test LLM's capacity for tool calling.

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
sys.path.append(str(Path(__file__).parent.parent / "tools"))

from .tool_registry import MultiToolRegistry
from .models import MultiToolName, MultiTool, MultiToolDecision, ToolCall
from shared_utils.llm_factory import setup_llm
import dspy
from pydantic import BaseModel, Field

# Import the selector
from .multi_tool_selector import MultiToolSelector

# Import shared utilities
from shared_utils import (
    ToolSelectionMetrics, 
    TestCase, 
    TestResult, 
    TestSummary,
    ToolSelectionEvaluation,
    ConsoleFormatter
)
from .test_cases import get_multi_tool_test_cases


def run_demo(verbose=True, predict=False):
    """Run the multi-tool demo and return results as a dictionary.
    
    Args:
        verbose: If True, print progress to console. If False, run quietly.
        predict: If True, use dspy.Predict instead of dspy.ChainOfThought
        
    Returns:
        Dictionary containing summary and detailed results
    """
    start_time = time.time()
    formatter = ConsoleFormatter()
    metrics = ToolSelectionMetrics()
    
    if verbose:
        print(formatter.section_header("🚀 DSPy Multi-Tool Selection Demo"))
        print("Testing LLM's capacity for multi-tool selection from 14 available tools")
        print(f"Mode: {'dspy.Predict' if predict else 'dspy.ChainOfThought'}\n")
    
    # Setup
    try:
        if verbose:
            setup_llm()
        else:
            # Suppress output
            import io
            import contextlib
            with contextlib.redirect_stdout(io.StringIO()):
                setup_llm()
    except Exception as e:
        if verbose:
            print(formatter.error_message(f"Failed to setup Ollama: {e}"))
        return {"error": f"Failed to setup Ollama: {e}"}
    
    # Initialize registry and selector
    registry = MultiToolRegistry()
    registry.register_all_tools()
    selector = MultiToolSelector(use_predict=predict)
    
    # Get test cases from shared module
    test_cases = get_multi_tool_test_cases()
    
    # Track results
    test_results = []
    evaluations = []
    
    if verbose:
        print(formatter.section_separator())
    
    for i, test_case in enumerate(test_cases, 1):
        test_start = time.time()
        
        if verbose:
            print(formatter.test_progress(i, len(test_cases), test_case.description))
            print(f"👤 User: {test_case.request}")
            print(f"🎯 Expected tools: {test_case.expected_tools}")
        
        try:
            # Get LLM's decision
            decision = selector(test_case.request, registry.get_tool_definitions())
            
            # Extract actual tools selected
            actual_tools = [tc.tool_name for tc in decision.tool_calls]
            
            if verbose:
                print(f"\n🤖 Selected tools: {actual_tools}")
                print(f"   Reasoning: {decision.reasoning}")
            
            # Evaluate selection using shared metrics
            expected_set = set(test_case.expected_tools)
            actual_set = set(actual_tools)
            evaluation = metrics.evaluate_selection(expected_set, actual_set)
            
            # Create evaluation object
            eval_obj = ToolSelectionEvaluation(**evaluation)
            
            if verbose:
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
                results = registry.execute(decision)
                execution_results = results
                
                if verbose:
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
                if verbose:
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
            
            if verbose:
                error_msg = f'Selection error: {e}'
                print(f"   {formatter.error_message(error_msg)}")
            
        if verbose:
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
    
    if verbose:
        # Print summary using formatter
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
        
        # Show debug history if enabled
        debug = os.getenv("DSPY_DEBUG", "false").lower() == "true"
        if debug:
            print(f"\n{formatter.section_header('🔍 DSPy Execution History (last 3 calls)')}")
            dspy.inspect_history(n=3)
            print(formatter.section_separator())
        
        print(formatter.success_message("\n✅ Multi-tool demo complete!"))
    
    # Return results in format compatible with existing code
    return {
        "summary": summary.model_dump(),
        "detailed_results": [r.model_dump() for r in test_results],
        "model": summary.model,
        "timestamp": summary.timestamp.isoformat()
    }


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run multi-tool selection demo")
    parser.add_argument("--predict", action="store_true", 
                        help="Use dspy.Predict instead of dspy.ChainOfThought")
    parser.add_argument("--quiet", action="store_true",
                        help="Run in quiet mode without verbose output")
    
    args = parser.parse_args()
    
    results = run_demo(verbose=not args.quiet, predict=args.predict)
    
    # Optionally save to file when run standalone
    if 'error' not in results:
        with open('test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        if not args.quiet:
            print(f"\n💾 Results saved to: test_results.json")


if __name__ == "__main__":
    main()