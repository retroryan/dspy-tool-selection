#!/usr/bin/env poetry run python3
"""Convert model comparison CSV results to a markdown summary."""

import sys
import pandas as pd
from pathlib import Path
import argparse
from datetime import datetime


def generate_markdown_summary(csv_path: str) -> str:
    """Generate a markdown summary from the CSV results."""
    # Read the CSV
    df = pd.read_csv(csv_path)
    
    # Filter out any error results for main analysis
    success_df = df[df['status'] == 'success'].copy()
    
    if success_df.empty:
        return "# Model Comparison Results\n\nNo successful test results found."
    
    # Sort by F1 score
    success_df = success_df.sort_values('avg_f1', ascending=False)
    
    # Get unique models
    models = success_df['model'].unique()
    
    # Start building markdown
    md = []
    md.append("# DSPy Tool Selection Model Comparison Results")
    md.append("")
    md.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append(f"**Source**: `{Path(csv_path).name}`")
    md.append("")
    
    # Executive Summary
    md.append("## Executive Summary")
    md.append("")
    
    best_result = success_df.iloc[0]
    md.append(f"**Best Configuration**: {best_result['model']} ({best_result['mode']})")
    md.append(f"- F1 Score: {best_result['avg_f1']:.3f}")
    md.append(f"- Perfect Matches: {int(best_result['perfect_matches'])}/{int(best_result['total_tests'])} ({best_result['perfect_match_pct']:.1f}%)")
    md.append(f"- Precision: {best_result['avg_precision']:.3f}")
    md.append(f"- Recall: {best_result['avg_recall']:.3f}")
    md.append("")
    
    # Overall Rankings Table
    md.append("## Overall Performance Rankings")
    md.append("")
    md.append("| Rank | Model | Mode | F1 Score | Precision | Recall | Perfect Matches | Runtime |")
    md.append("|------|-------|------|----------|-----------|--------|----------------|---------|")
    
    for idx, row in success_df.iterrows():
        rank = len(success_df[success_df['avg_f1'] > row['avg_f1']]) + 1
        perfect_str = f"{int(row['perfect_matches'])}/{int(row['total_tests'])} ({row['perfect_match_pct']:.1f}%)"
        md.append(f"| {rank} | {row['model']} | {row['mode']} | {row['avg_f1']:.3f} | {row['avg_precision']:.3f} | {row['avg_recall']:.3f} | {perfect_str} | {row['runtime']:.1f}s |")
    
    md.append("")
    
    # Mode Comparison by Model
    md.append("## Mode Comparison by Model")
    md.append("")
    
    for model in models:
        model_results = success_df[success_df['model'] == model]
        
        if len(model_results) >= 2:
            md.append(f"### {model}")
            md.append("")
            
            # Try to get both modes
            cot_results = model_results[model_results['mode'] == 'ChainOfThought']
            pred_results = model_results[model_results['mode'] == 'Predict']
            
            if not cot_results.empty and not pred_results.empty:
                cot = cot_results.iloc[0]
                pred = pred_results.iloc[0]
                
                # Create comparison table
                md.append("| Metric | ChainOfThought | Predict | Difference |")
                md.append("|--------|----------------|---------|------------|")
                
                # F1 Score
                f1_diff = cot['avg_f1'] - pred['avg_f1']
                f1_winner = "🏆" if f1_diff > 0 else ("" if f1_diff == 0 else "")
                f1_winner_pred = "🏆" if f1_diff < 0 else ""
                md.append(f"| F1 Score | {cot['avg_f1']:.3f} {f1_winner} | {pred['avg_f1']:.3f} {f1_winner_pred} | {abs(f1_diff):.3f} |")
                
                # Precision
                prec_diff = cot['avg_precision'] - pred['avg_precision']
                md.append(f"| Precision | {cot['avg_precision']:.3f} | {pred['avg_precision']:.3f} | {abs(prec_diff):.3f} |")
                
                # Recall
                recall_diff = cot['avg_recall'] - pred['avg_recall']
                md.append(f"| Recall | {cot['avg_recall']:.3f} | {pred['avg_recall']:.3f} | {abs(recall_diff):.3f} |")
                
                # Perfect Matches
                perfect_cot = f"{int(cot['perfect_matches'])}/{int(cot['total_tests'])}"
                perfect_pred = f"{int(pred['perfect_matches'])}/{int(pred['total_tests'])}"
                md.append(f"| Perfect Matches | {perfect_cot} | {perfect_pred} | - |")
                
                # Runtime
                runtime_diff = cot['runtime'] - pred['runtime']
                md.append(f"| Runtime | {cot['runtime']:.1f}s | {pred['runtime']:.1f}s | {abs(runtime_diff):.1f}s |")
                
                md.append("")
                
                # Summary
                if f1_diff > 0.01:
                    md.append(f"**Summary**: ChainOfThought outperforms Predict by {f1_diff:.3f} F1 points")
                elif f1_diff < -0.01:
                    md.append(f"**Summary**: Predict outperforms ChainOfThought by {abs(f1_diff):.3f} F1 points")
                else:
                    md.append("**Summary**: Both modes perform similarly")
                
                md.append("")
    
    # Key Insights
    md.append("## Key Insights")
    md.append("")
    
    # Calculate aggregate statistics
    cot_avg_f1 = success_df[success_df['mode'] == 'ChainOfThought']['avg_f1'].mean()
    pred_avg_f1 = success_df[success_df['mode'] == 'Predict']['avg_f1'].mean()
    
    cot_avg_runtime = success_df[success_df['mode'] == 'ChainOfThought']['runtime'].mean()
    pred_avg_runtime = success_df[success_df['mode'] == 'Predict']['runtime'].mean()
    
    md.append("### Overall Mode Performance")
    md.append("")
    md.append(f"- **Average F1 Score**:")
    md.append(f"  - ChainOfThought: {cot_avg_f1:.3f}")
    md.append(f"  - Predict: {pred_avg_f1:.3f}")
    md.append(f"- **Average Runtime**:")
    md.append(f"  - ChainOfThought: {cot_avg_runtime:.1f}s")
    md.append(f"  - Predict: {pred_avg_runtime:.1f}s")
    md.append("")
    
    # Models where each mode wins
    md.append("### Mode Advantages by Model")
    md.append("")
    
    cot_wins = []
    pred_wins = []
    ties = []
    
    for model in models:
        model_results = success_df[success_df['model'] == model]
        cot_results = model_results[model_results['mode'] == 'ChainOfThought']
        pred_results = model_results[model_results['mode'] == 'Predict']
        
        if not cot_results.empty and not pred_results.empty:
            cot_f1 = cot_results.iloc[0]['avg_f1']
            pred_f1 = pred_results.iloc[0]['avg_f1']
            
            if cot_f1 > pred_f1 + 0.01:
                cot_wins.append(model)
            elif pred_f1 > cot_f1 + 0.01:
                pred_wins.append(model)
            else:
                ties.append(model)
    
    if cot_wins:
        md.append(f"- **ChainOfThought performs better on**: {', '.join(cot_wins)}")
    if pred_wins:
        md.append(f"- **Predict performs better on**: {', '.join(pred_wins)}")
    if ties:
        md.append(f"- **Similar performance on**: {', '.join(ties)}")
    
    md.append("")
    
    # Test Details
    if 'total_tests' in success_df.columns and success_df['total_tests'].nunique() == 1:
        total_tests = int(success_df['total_tests'].iloc[0])
        md.append("## Test Details")
        md.append("")
        md.append(f"- **Total test cases per configuration**: {total_tests}")
        md.append("- **Test categories**: Multi-tool selection across events, e-commerce, and finance domains")
        md.append("- **Evaluation metrics**:")
        md.append("  - **F1 Score**: Harmonic mean of precision and recall")
        md.append("  - **Precision**: Fraction of selected tools that were correct")
        md.append("  - **Recall**: Fraction of expected tools that were selected")
        md.append("  - **Perfect Matches**: Test cases where exactly the right tools were selected")
    
    md.append("")
    
    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description='Convert model comparison CSV to markdown summary')
    parser.add_argument('csv_file', help='Path to the CSV file')
    parser.add_argument('-o', '--output', help='Output markdown file (default: <csv_name>_summary.md)')
    
    args = parser.parse_args()
    
    # Check if CSV exists
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"Error: CSV file '{csv_path}' not found")
        sys.exit(1)
    
    # Generate markdown
    try:
        markdown_content = generate_markdown_summary(str(csv_path))
    except Exception as e:
        print(f"Error processing CSV: {e}")
        sys.exit(1)
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = csv_path.parent / f"{csv_path.stem}_summary.md"
    
    # Write markdown file
    output_path.write_text(markdown_content)
    print(f"✅ Markdown summary written to: {output_path}")
    
    # Also print to console
    print("\n" + "="*80)
    print("MARKDOWN PREVIEW")
    print("="*80 + "\n")
    print(markdown_content)


if __name__ == "__main__":
    main()