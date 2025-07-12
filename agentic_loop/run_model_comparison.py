#!/usr/bin/env poetry run python3
"""
Run the agentic loop demo with multiple Ollama models and compare results.

This script automates the process of evaluating different Ollama language models
on their ability to perform multi-tool selection within the agentic loop architecture.
It runs the agent_loop_demo for each specified model and aggregates performance metrics.
"""

import subprocess
import sys
import os
import json
import pandas as pd
from datetime import datetime
import time
from typing import Dict, List, Any
import argparse
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentic_loop.agent_loop_demo import run_agent_loop_demo
from shared_utils import ConsoleFormatter


def check_prerequisites():
    """Check if all prerequisites are met."""
    print("🔍 Checking prerequisites...")
    
    # Check if Ollama is running
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/tags"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("❌ Ollama is not running. Please start it with: ollama serve")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        sys.exit(1)
    
    print("✅ All prerequisites met\n")


def get_ollama_models() -> List[str]:
    """Get list of available Ollama models."""
    print("📋 Getting list of Ollama models...")
    
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("❌ Failed to get Ollama models")
            return []
        
        # Parse the output to get model names
        lines = result.stdout.strip().split('\n')
        models = []
        
        # Skip the header line
        for line in lines[1:]:
            if line.strip():
                # Model name is the first column
                model_name = line.split()[0]
                models.append(model_name)
        
        print(f"✅ Found {len(models)} models: {', '.join(models)}\n")
        return models
        
    except Exception as e:
        print(f"❌ Error getting models: {e}")
        return []


def load_ollama_model(model: str) -> bool:
    """Load an Ollama model, ensuring it's available for use."""
    print(f"📥 Loading model: {model}...")
    try:
        # First, try to pull the model in case it's not downloaded
        result = subprocess.run(
            ["ollama", "pull", model],
            capture_output=True,
            text=True
        )
        if result.returncode != 0 and "already up to date" not in result.stdout:
            print(f"⚠️  Warning pulling model: {result.stderr}")
        
        # Load the model into memory
        result = subprocess.run(
            ["ollama", "run", model, "exit"],
            input="exit\n",
            capture_output=True,
            text=True
        )
        print(f"✅ Model {model} loaded")
        return True
    except Exception as e:
        print(f"❌ Error loading model {model}: {e}")
        return False


def unload_ollama_model(model: str):
    """Unload an Ollama model to free up memory."""
    print(f"📤 Unloading model: {model}...")
    try:
        # There's no direct unload command, but we can let Ollama manage memory
        print(f"✅ Finished with model {model}")
    except Exception as e:
        print(f"⚠️  Warning unloading model: {e}")


def run_agentic_loop_for_model(model: str, tool_set: str) -> Dict[str, Any]:
    """Run the agentic loop demo for a specific model and capture results.
    
    Args:
        model: The Ollama model name
        tool_set: The tool set to test with
    """
    print(f"\n{'='*80}")
    print(f"🚀 Testing model: {model} with tool set: {tool_set}")
    print(f"{'='*80}\n")
    
    # Set the model in environment
    os.environ['OLLAMA_MODEL'] = model
    os.environ['DSPY_DEBUG'] = 'false'  # Disable debug for cleaner output
    
    start_time = time.time()
    
    try:
        # Run the demo directly
        output_data = run_agent_loop_demo(tool_set_name=tool_set)
        
        if 'error' in output_data:
            print(f"❌ Error running demo: {output_data['error']}")
            return {
                'model': model,
                'tool_set': tool_set,
                'status': 'error',
                'error': output_data['error'],
                'runtime': time.time() - start_time
            }
        
        summary = output_data['summary']
        
        summary_results = {
            'model': model,
            'tool_set': tool_set,
            'status': 'success',
            'runtime': time.time() - start_time,
            'total_tests': summary['total_tests'],
            'perfect_matches': summary['perfect_matches'],
            'perfect_match_pct': (summary['perfect_matches'] / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0,
            'avg_precision': summary['avg_precision'],
            'avg_recall': summary['avg_recall'],
            'avg_f1': summary['avg_f1_score'],
            'passed_tests': summary['passed_tests'],
            'success_rate': summary['success_rate']
        }
        
        # Print brief summary
        print(f"\n📊 Quick Summary for {model}:")
        print(f"   Tool set: {tool_set}")
        print(f"   Perfect matches: {summary_results['perfect_matches']}/{summary_results['total_tests']} ({summary_results['perfect_match_pct']:.1f}%)")
        print(f"   F1 Score: {summary_results['avg_f1']:.2f}")
        print(f"   Success rate: {summary_results['success_rate']:.1f}%")
        
        return summary_results
        
    except Exception as e:
        print(f"❌ Exception running demo: {e}")
        return {
            'model': model,
            'tool_set': tool_set,
            'status': 'error',
            'error': str(e),
            'runtime': time.time() - start_time
        }


def main():
    """Main function to run the comparison."""
    parser = argparse.ArgumentParser(description='Run multi-model comparison for DSPy agentic loop')
    parser.add_argument('tool_set', nargs='?', default='productivity',
                        choices=['treasure_hunt', 'productivity', 'ecommerce'],
                        help='Tool set to test models against (default: productivity)')
    parser.add_argument('--models', type=str, help='Comma-separated list of models to test')
    args = parser.parse_args()
    
    formatter = ConsoleFormatter()
    print(formatter.section_header("🚀 DSPy Agentic Loop - Multi-Model Comparison"))
    
    # Check prerequisites
    check_prerequisites()
    
    # Get available models
    available_models = get_ollama_models()
    
    if not available_models:
        print("❌ No Ollama models found")
        sys.exit(1)
    
    # Determine which models to test
    if args.models:
        # Parse comma-separated models
        models_to_test = [m.strip() for m in args.models.split(',')]
        
        # Validate that requested models are available
        invalid_models = [m for m in models_to_test if m not in available_models]
        if invalid_models:
            print(f"❌ Error: The following models are not available: {', '.join(invalid_models)}")
            print(f"   Available models: {', '.join(available_models)}")
            sys.exit(1)
    else:
        # Default: test a predefined set of models
        default_models = ['gemma3:27b', 'llama3.1:8b']
        models_to_test = [m for m in default_models if m in available_models]
        
        if not models_to_test:
            print(f"❌ None of the default models {default_models} are available")
            print(f"   Available models: {', '.join(available_models)}")
            print(f"   Please specify models with --models option")
            sys.exit(1)
    
    print(f"\n📊 Testing {len(models_to_test)} models with tool set: {args.tool_set}")
    print(f"   Models: {', '.join(models_to_test)}")
    print(f"   Tool set: {args.tool_set}\n")
    
    # Run tests for each model
    results = []
    for model in models_to_test:
        # Check if model exists in available models
        if model not in available_models:
            print(f"⚠️  Model {model} not found, skipping...")
            continue
            
        # Load the model before testing
        if not load_ollama_model(model):
            print(f"❌ Failed to load {model}, skipping...")
            continue
        
        try:
            # Run the agentic loop demo
            result = run_agentic_loop_for_model(model, args.tool_set)
            results.append(result)
        finally:
            # Always unload the model after testing
            unload_ollama_model(model)
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Sort by F1 score (best first)
    if 'avg_f1' in df.columns:
        df = df.sort_values('avg_f1', ascending=False)
    
    # Display results
    print(formatter.section_header("📊 FINAL MODEL COMPARISON RESULTS"))
    
    # Display key columns
    display_columns = ['model', 'tool_set', 'status', 'total_tests', 'passed_tests', 
                      'perfect_matches', 'perfect_match_pct', 'avg_precision', 
                      'avg_recall', 'avg_f1', 'success_rate', 'runtime']
    available_columns = [col for col in display_columns if col in df.columns]
    
    # Format the dataframe for display
    df_display = df[available_columns].copy()
    if 'runtime' in df_display.columns:
        df_display['runtime'] = df_display['runtime'].apply(lambda x: f"{x:.1f}s")
    
    # Rename columns for better display
    column_rename = {
        'total_tests': 'tests',
        'passed_tests': 'passed',
        'perfect_matches': 'perfect',
        'perfect_match_pct': 'perfect%',
        'avg_precision': 'precision',
        'avg_recall': 'recall',
        'avg_f1': 'F1',
        'success_rate': 'success%'
    }
    df_display = df_display.rename(columns=column_rename)
    
    print(df_display.to_string(index=False, float_format='%.2f'))
    
    # Create results directory if it doesn't exist
    results_dir = Path("test_results")
    results_dir.mkdir(exist_ok=True)
    
    # Save to JSON in the results directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = results_dir / f"model_comparison_{args.tool_set}_{timestamp}.json"
    
    # Save detailed results
    results_data = {
        'tool_set': args.tool_set,
        'timestamp': timestamp,
        'models_tested': models_to_test,
        'results': results
    }
    
    with open(json_filename, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\n💾 Results saved to: {json_filename}")
    
    # Create a visual summary
    if 'avg_f1' in df.columns and len(df[df['status'] == 'success']) > 0:
        print(formatter.section_header("📈 PERFORMANCE RANKINGS (by F1 Score)"))
        
        success_df = df[df['status'] == 'success'].copy()
        for idx, row in success_df.iterrows():
            # Create a visual bar for F1 score
            bar = formatter.performance_bar(row['avg_f1'])
            print(f"{row['model']:30} {bar} {row['avg_f1']:.2f}")
        
        print(f"\n{formatter.section_separator()}")
        best_model = success_df.iloc[0]
        print(formatter.success_message(f"🏆 Best model: {best_model['model']}"))
        print(f"   - Tool set: {best_model['tool_set']}")
        print(f"   - F1 Score: {best_model['avg_f1']:.2f}")
        print(f"   - Precision: {best_model['avg_precision']:.2f}")
        print(f"   - Recall: {best_model['avg_recall']:.2f}")
        print(f"   - Perfect matches: {int(best_model['perfect_matches'])}/{int(best_model['total_tests'])} ({best_model['perfect_match_pct']:.1f}%)")
        print(f"   - Success rate: {best_model['success_rate']:.1f}%")
        print(f"   - Runtime: {best_model['runtime']:.1f}s")
        
        print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()