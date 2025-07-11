#!/usr/bin/env poetry run python3
"""Run the multi-tool demo with multiple Ollama models and compare results."""

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

from tool_selection.multi_demo import run_demo
from shared_utils import ConsoleFormatter, TestSummary, ModelComparisonResult

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
        # There's no direct unload command, but we can load a tiny model to clear memory
        # Alternatively, we can just let Ollama manage memory automatically
        # For now, we'll just print that we're done with the model
        print(f"✅ Finished with model {model}")
    except Exception as e:
        print(f"⚠️  Warning unloading model: {e}")


def run_multi_demo_for_model(model: str, predict_mode: bool) -> Dict[str, Any]:
    """Run the multi-tool demo for a specific model and capture results.
    
    Args:
        model: The Ollama model name
        predict_mode: If True, use dspy.Predict, else use dspy.ChainOfThought
    """
    mode_name = "Predict" if predict_mode else "ChainOfThought"
    print(f"\n{'='*80}")
    print(f"🚀 Testing model: {model} (Mode: {mode_name})")
    print(f"{'='*80}\n")
    
    # Set the model in environment
    os.environ['OLLAMA_MODEL'] = model
    os.environ['DSPY_DEBUG'] = 'false'  # Disable debug for cleaner output
    
    start_time = time.time()
    
    try:
        # Run the demo directly with predict parameter
        output_data = run_demo(verbose=True, predict=predict_mode)
        
        if 'error' in output_data:
            print(f"❌ Error running demo: {output_data['error']}")
            return {
                'model': model,
                'mode': mode_name,
                'status': 'error',
                'error': output_data['error'],
                'runtime': time.time() - start_time
            }
        
        summary = output_data['summary']
        
        summary_results = {
            'model': model,
            'mode': mode_name,
            'status': 'success',
            'runtime': time.time() - start_time,
            'total_tests': summary['total_tests'],
            'perfect_matches': summary['perfect_matches'],
            'perfect_match_pct': (summary['perfect_matches'] / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0,
            'avg_precision': summary['avg_precision'],
            'avg_recall': summary['avg_recall'],
            'avg_f1': summary['avg_f1_score']
        }
        
        # Print brief summary
        print(f"\n📊 Quick Summary for {model} ({mode_name}):")
        print(f"   Perfect matches: {summary_results['perfect_matches']}/{summary_results['total_tests']} ({summary_results['perfect_match_pct']:.1f}%)")
        print(f"   F1 Score: {summary_results['avg_f1']:.2f}")
        
        return summary_results
        
    except Exception as e:
        print(f"❌ Exception running demo: {e}")
        return {
            'model': model,
            'mode': mode_name,
            'status': 'error',
            'error': str(e),
            'runtime': time.time() - start_time
        }


def main():
    """Main function to run the comparison."""
    parser = argparse.ArgumentParser(description='Run multi-model comparison for DSPy tool selection')
    parser.add_argument('--models', type=str, help='Comma-separated list of models to test')
    args = parser.parse_args()
    
    formatter = ConsoleFormatter()
    print(formatter.section_header("🚀 DSPy Multi-Tool Selection - Multi-Model & Mode Comparison"))
    
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
        models_to_test = ['gemma3:27b']
    
    print(f"\n📊 Testing {len(models_to_test)} models with both Predict and ChainOfThought modes")
    print(f"   Models: {', '.join(models_to_test)}")
    print(f"   Total tests: {len(models_to_test) * 2} (each model × 2 modes)\n")
    
    # Run tests for each model with both modes
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
            # Run with ChainOfThought (default)
            result_cot = run_multi_demo_for_model(model, predict_mode=False)
            results.append(result_cot)
            
            # Run with Predict
            result_predict = run_multi_demo_for_model(model, predict_mode=True)
            results.append(result_predict)
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
    
    # Display key columns - include mode and total_tests
    display_columns = ['model', 'mode', 'status', 'total_tests', 'perfect_matches', 'perfect_match_pct', 
                      'avg_precision', 'avg_recall', 'avg_f1', 'runtime']
    available_columns = [col for col in display_columns if col in df.columns]
    
    # Format the dataframe for display
    df_display = df[available_columns].copy()
    if 'runtime' in df_display.columns:
        df_display['runtime'] = df_display['runtime'].apply(lambda x: f"{x:.1f}s")
    
    # Rename columns for better display
    column_rename = {
        'total_tests': 'tests',
        'perfect_matches': 'perfect',
        'perfect_match_pct': 'perfect%',
        'avg_precision': 'precision',
        'avg_recall': 'recall',
        'avg_f1': 'F1'
    }
    df_display = df_display.rename(columns=column_rename)
    
    print(df_display.to_string(index=False, float_format='%.2f'))
    
    # Create results directory if it doesn't exist
    results_dir = Path("model_test_results")
    results_dir.mkdir(exist_ok=True)
    
    # Save to CSV in the results directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = results_dir / f"model_comparison_{timestamp}.csv"
    df.to_csv(csv_filename, index=False)
    print(f"\n💾 Results saved to: {csv_filename}")
    
    # Create a visual summary
    if 'avg_f1' in df.columns and len(df[df['status'] == 'success']) > 0:
        print(formatter.section_header("📈 PERFORMANCE RANKINGS (by F1 Score)"))
        
        success_df = df[df['status'] == 'success'].copy()
        for idx, row in success_df.iterrows():
            # Create a visual bar for F1 score
            bar = formatter.performance_bar(row['avg_f1'])
            
            mode_display = f"({row['mode']})" if 'mode' in row else ""
            print(f"{row['model']:20} {mode_display:16} {bar} {row['avg_f1']:.2f}")
        
        print(f"\n{formatter.section_separator()}")
        best_model = success_df.iloc[0]
        mode_info = f" ({best_model['mode']})" if 'mode' in best_model else ""
        print(formatter.success_message(f"🏆 Best configuration: {best_model['model']}{mode_info}"))
        print(f"   - F1 Score: {best_model['avg_f1']:.2f}")
        print(f"   - Precision: {best_model['avg_precision']:.2f}")
        print(f"   - Recall: {best_model['avg_recall']:.2f}")
        print(f"   - Perfect matches: {int(best_model['perfect_matches'])}/{int(best_model['total_tests'])} ({best_model['perfect_match_pct']:.1f}%)")
        print(f"   - Runtime: {best_model['runtime']:.1f}s")
        
        # Compare modes for each model
        print(formatter.section_header("📊 MODE COMPARISON BY MODEL"))
        
        # Get unique models that were actually tested
        tested_models = success_df['model'].unique()
        
        for model in tested_models:
            model_results = success_df[success_df['model'] == model]
            if len(model_results) == 2:
                cot_result = model_results[model_results['mode'] == 'ChainOfThought'].iloc[0]
                pred_result = model_results[model_results['mode'] == 'Predict'].iloc[0]
                
                print(f"{model}:")
                print(f"   ChainOfThought: F1={cot_result['avg_f1']:.2f}, Perfect={int(cot_result['perfect_matches'])}/{int(cot_result['total_tests'])}")
                print(f"   Predict:        F1={pred_result['avg_f1']:.2f}, Perfect={int(pred_result['perfect_matches'])}/{int(pred_result['total_tests'])}")
                
                # Show which mode is better
                if cot_result['avg_f1'] > pred_result['avg_f1']:
                    diff = cot_result['avg_f1'] - pred_result['avg_f1']
                    print(f"   → ChainOfThought is better by {diff:.2f} F1 points\n")
                elif pred_result['avg_f1'] > cot_result['avg_f1']:
                    diff = pred_result['avg_f1'] - cot_result['avg_f1']
                    print(f"   → Predict is better by {diff:.2f} F1 points\n")
                else:
                    print(f"   → Both modes perform equally\n")
        
        print(f"{'='*80}\n")

if __name__ == "__main__":
    main()