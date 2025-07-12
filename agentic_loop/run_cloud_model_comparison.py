#!/usr/bin/env poetry run python3
"""
Run the agentic loop demo with multiple cloud models (Claude and OpenAI) and compare results.

This script automates the process of evaluating different cloud language models
on their ability to perform multi-tool selection within the agentic loop architecture.
"""

import subprocess
import sys
import os
import json
import pandas as pd
from datetime import datetime
import time
from typing import Dict, List, Any, Tuple
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentic_loop.agent_loop_demo import run_agent_loop_demo
from shared_utils import ConsoleFormatter


# Default cloud models (used when no specific models are requested)
# Users can specify any model IDs - these are just the defaults
CLOUD_MODELS = {
    'claude': [
        ('claude-3-haiku-20240307', 'Claude 3 Haiku'),
        ('claude-3-sonnet-20240229', 'Claude 3 Sonnet'),
    ],
    'openai': [
        ('gpt-4', 'GPT-4'),
        ('gpt-3.5-turbo', 'GPT-3.5 Turbo'),
    ]
}


def check_prerequisites():
    """Check if all prerequisites are met."""
    print("🔍 Checking prerequisites...")
    
    # Check if cloud_test.env exists
    if not os.path.exists('cloud_test.env'):
        print("❌ cloud_test.env not found. Please create it with your API keys.")
        sys.exit(1)
    
    # Load the environment file
    load_dotenv('cloud_test.env', override=True)
    
    # Check for API keys
    has_claude = bool(os.getenv('ANTHROPIC_API_KEY'))
    has_openai = bool(os.getenv('OPENAI_API_KEY'))
    
    if not has_claude and not has_openai:
        print("❌ No API keys found in cloud_test.env")
        print("   Please add ANTHROPIC_API_KEY and/or OPENAI_API_KEY")
        sys.exit(1)
    
    print("✅ All prerequisites met")
    if has_claude:
        print("   ✓ Claude API key found")
    if has_openai:
        print("   ✓ OpenAI API key found")
    print()


def run_agentic_loop_for_cloud_model(provider: str, model: str, model_name: str, tool_set: str) -> Dict[str, Any]:
    """Run the agentic loop demo for a specific cloud model and capture results.
    
    Args:
        provider: The provider (claude or openai)
        model: The model ID
        model_name: Human-readable model name
        tool_set: The tool set to test with
    """
    print(f"\n{'='*80}")
    print(f"🚀 Testing model: {model_name} ({provider}) with tool set: {tool_set}")
    print(f"{'='*80}\n")
    
    # Set the provider and model in environment
    os.environ['DSPY_PROVIDER'] = provider
    
    if provider == 'claude':
        os.environ['CLAUDE_MODEL'] = model
    elif provider == 'openai':
        os.environ['OPENAI_MODEL'] = model
    
    os.environ['DSPY_DEBUG'] = 'false'  # Disable debug for cleaner output
    
    start_time = time.time()
    
    try:
        # Run the demo directly
        output_data = run_agent_loop_demo(tool_set_name=tool_set)
        
        if 'error' in output_data:
            print(f"❌ Error running demo: {output_data['error']}")
            return {
                'provider': provider,
                'model': model,
                'model_name': model_name,
                'tool_set': tool_set,
                'status': 'error',
                'error': output_data['error'],
                'runtime': time.time() - start_time
            }
        
        summary = output_data['summary']
        
        summary_results = {
            'provider': provider,
            'model': model,
            'model_name': model_name,
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
        print(f"\n📊 Quick Summary for {model_name}:")
        print(f"   Provider: {provider}")
        print(f"   Tool set: {tool_set}")
        print(f"   Perfect matches: {summary_results['perfect_matches']}/{summary_results['total_tests']} ({summary_results['perfect_match_pct']:.1f}%)")
        print(f"   F1 Score: {summary_results['avg_f1']:.2f}")
        print(f"   Success rate: {summary_results['success_rate']:.1f}%")
        
        return summary_results
        
    except Exception as e:
        print(f"❌ Exception running demo: {e}")
        return {
            'provider': provider,
            'model': model,
            'model_name': model_name,
            'tool_set': tool_set,
            'status': 'error',
            'error': str(e),
            'runtime': time.time() - start_time
        }


def main():
    """Main function to run the comparison."""
    parser = argparse.ArgumentParser(description='Run cloud model comparison for DSPy agentic loop')
    parser.add_argument('tool_set', nargs='?', default='productivity',
                        choices=['treasure_hunt', 'productivity', 'ecommerce'],
                        help='Tool set to test models against (default: productivity)')
    parser.add_argument('--providers', type=str, help='Comma-separated list of providers to test (claude,openai)')
    parser.add_argument('--models', type=str, help='Comma-separated list of specific models to test')
    args = parser.parse_args()
    
    formatter = ConsoleFormatter()
    print(formatter.section_header("🚀 DSPy Agentic Loop - Cloud Model Comparison"))
    
    # Check prerequisites and load environment
    check_prerequisites()
    
    # Determine which providers to test
    available_providers = []
    if os.getenv('ANTHROPIC_API_KEY'):
        available_providers.append('claude')
    if os.getenv('OPENAI_API_KEY'):
        available_providers.append('openai')
    
    if args.providers:
        # Use specified providers
        providers_to_test = [p.strip() for p in args.providers.split(',')]
        # Validate providers
        invalid_providers = [p for p in providers_to_test if p not in available_providers]
        if invalid_providers:
            print(f"❌ Error: The following providers are not available: {', '.join(invalid_providers)}")
            print(f"   Available providers: {', '.join(available_providers)}")
            sys.exit(1)
    else:
        # Use all available providers
        providers_to_test = available_providers
    
    # Collect models to test
    models_to_test = []
    
    if args.models:
        # Parse specific models from command line
        model_specs = [m.strip() for m in args.models.split(',')]
    elif os.getenv('CLOUD_TEST_MODELS'):
        # Parse models from environment variable
        model_specs = [m.strip() for m in os.getenv('CLOUD_TEST_MODELS').split(',')]
        print(f"📋 Using models from CLOUD_TEST_MODELS environment variable")
    else:
        # Use default models for each provider
        model_specs = None
    
    if model_specs:
        # Process specified models - auto-detect provider from model name
        for model_spec in model_specs:
            # Auto-detect provider based on model naming conventions
            if 'claude' in model_spec.lower():
                provider = 'claude'
            elif 'gpt' in model_spec.lower() or 'o1' in model_spec.lower():
                provider = 'openai'
            else:
                # Default fallback - could be extended for other providers
                provider = 'claude' if model_spec.startswith('claude') else 'openai'
            
            models_to_test.append((provider, model_spec, model_spec))
    else:
        # Use default models for each provider
        for provider in providers_to_test:
            if provider in CLOUD_MODELS:
                # Take first 2 models from each provider
                for model_id, model_name in CLOUD_MODELS[provider][:2]:
                    models_to_test.append((provider, model_id, model_name))
    
    if not models_to_test:
        print("❌ No models to test")
        sys.exit(1)
    
    print(f"\n📊 Testing {len(models_to_test)} models with tool set: {args.tool_set}")
    print("   Models:")
    for provider, model_id, model_name in models_to_test:
        print(f"     - {model_name} ({provider})")
    print(f"   Tool set: {args.tool_set}\n")
    
    # Run tests for each model
    results = []
    for provider, model_id, model_name in models_to_test:
        # Check if we have the API key for this provider
        if provider == 'claude' and not os.getenv('ANTHROPIC_API_KEY'):
            print(f"⚠️  Skipping {model_name} - no Claude API key")
            continue
        elif provider == 'openai' and not os.getenv('OPENAI_API_KEY'):
            print(f"⚠️  Skipping {model_name} - no OpenAI API key")
            continue
        
        # Run the agentic loop demo
        result = run_agentic_loop_for_cloud_model(provider, model_id, model_name, args.tool_set)
        results.append(result)
        
        # Small delay between API calls to be respectful
        time.sleep(2)
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Sort by F1 score (best first)
    if 'avg_f1' in df.columns:
        df = df.sort_values('avg_f1', ascending=False)
    
    # Display results
    print(formatter.section_header("📊 FINAL CLOUD MODEL COMPARISON RESULTS"))
    
    # Display key columns
    display_columns = ['model_name', 'provider', 'status', 'total_tests', 'passed_tests', 
                      'perfect_matches', 'perfect_match_pct', 'avg_precision', 
                      'avg_recall', 'avg_f1', 'success_rate', 'runtime']
    available_columns = [col for col in display_columns if col in df.columns]
    
    # Format the dataframe for display
    df_display = df[available_columns].copy()
    if 'runtime' in df_display.columns:
        df_display['runtime'] = df_display['runtime'].apply(lambda x: f"{x:.1f}s")
    
    # Rename columns for better display
    column_rename = {
        'model_name': 'Model',
        'provider': 'Provider',
        'total_tests': 'Tests',
        'passed_tests': 'Passed',
        'perfect_matches': 'Perfect',
        'perfect_match_pct': 'Perfect%',
        'avg_precision': 'Precision',
        'avg_recall': 'Recall',
        'avg_f1': 'F1',
        'success_rate': 'Success%',
        'runtime': 'Runtime'
    }
    df_display = df_display.rename(columns=column_rename)
    
    print(df_display.to_string(index=False, float_format='%.2f'))
    
    # Create results directory if it doesn't exist
    results_dir = Path("test_results")
    results_dir.mkdir(exist_ok=True)
    
    # Save to JSON in the results directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = results_dir / f"cloud_model_comparison_{args.tool_set}_{timestamp}.json"
    
    # Save detailed results
    results_data = {
        'tool_set': args.tool_set,
        'timestamp': timestamp,
        'models_tested': [(p, m, n) for p, m, n in models_to_test],
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
            print(f"{row['model_name']:30} {bar} {row['avg_f1']:.2f}")
        
        print(f"\n{formatter.section_separator()}")
        best_model = success_df.iloc[0]
        print(formatter.success_message(f"🏆 Best model: {best_model['model_name']}"))
        print(f"   - Provider: {best_model['provider']}")
        print(f"   - Tool set: {args.tool_set}")
        print(f"   - F1 Score: {best_model['avg_f1']:.2f}")
        print(f"   - Precision: {best_model['avg_precision']:.2f}")
        print(f"   - Recall: {best_model['avg_recall']:.2f}")
        print(f"   - Perfect matches: {int(best_model['perfect_matches'])}/{int(best_model['total_tests'])} ({best_model['perfect_match_pct']:.1f}%)")
        print(f"   - Success rate: {best_model['success_rate']:.1f}%")
        print(f"   - Runtime: {best_model['runtime']:.1f}s")
        
        print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()