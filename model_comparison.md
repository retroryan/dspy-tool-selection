# DSPy Tool Selection Model Comparison Results

**Generated**: 2025-07-10 18:04:26
**Source**: `model_comparison_20250710_180050.csv`

## Executive Summary

**Best Configuration**: llama3.1:8b (ChainOfThought)
- F1 Score: 1.000
- Perfect Matches: 10/10 (100.0%)
- Precision: 1.000
- Recall: 1.000

## Overall Performance Rankings

| Rank | Model | Mode | F1 Score | Precision | Recall | Perfect Matches | Runtime |
|------|-------|------|----------|-----------|--------|----------------|---------|
| 1 | llama3.1:8b | ChainOfThought | 1.000 | 1.000 | 1.000 | 10/10 (100.0%) | 0.1s |
| 2 | deepseek-r1:14b | ChainOfThought | 0.967 | 1.000 | 0.950 | 9/10 (90.0%) | 236.2s |
| 3 | mistral:7b | ChainOfThought | 0.947 | 1.000 | 0.917 | 8/10 (80.0%) | 0.0s |
| 4 | gemma3:27b | ChainOfThought | 0.933 | 1.000 | 0.900 | 8/10 (80.0%) | 0.1s |
| 5 | llama3.1:8b | Predict | 0.930 | 0.950 | 0.917 | 8/10 (80.0%) | 57.2s |
| 5 | deepseek-r1:14b | Predict | 0.930 | 0.950 | 0.917 | 8/10 (80.0%) | 263.9s |
| 7 | mistral:7b | Predict | 0.917 | 0.950 | 0.900 | 8/10 (80.0%) | 79.1s |
| 8 | gemma3:27b | Predict | 0.893 | 1.000 | 0.833 | 6/10 (60.0%) | 0.0s |
| 9 | llama3.2:latest | ChainOfThought | 0.863 | 0.900 | 0.867 | 6/10 (60.0%) | 29.4s |
| 10 | deepseek-r1:8b | Predict | 0.850 | 1.000 | 0.783 | 6/10 (60.0%) | 264.4s |
| 11 | llama3.2:latest | Predict | 0.792 | 0.883 | 0.833 | 5/10 (50.0%) | 99.5s |
| 12 | deepseek-r1:8b | ChainOfThought | 0.763 | 0.850 | 0.717 | 5/10 (50.0%) | 223.6s |

## Mode Comparison by Model

### llama3.1:8b

| Metric | ChainOfThought | Predict | Difference |
|--------|----------------|---------|------------|
| F1 Score | 1.000 🏆 | 0.930  | 0.070 |
| Precision | 1.000 | 0.950 | 0.050 |
| Recall | 1.000 | 0.917 | 0.083 |
| Perfect Matches | 10/10 | 8/10 | - |
| Runtime | 0.1s | 57.2s | 57.1s |

**Summary**: ChainOfThought outperforms Predict by 0.070 F1 points

### deepseek-r1:14b

| Metric | ChainOfThought | Predict | Difference |
|--------|----------------|---------|------------|
| F1 Score | 0.967 🏆 | 0.930  | 0.037 |
| Precision | 1.000 | 0.950 | 0.050 |
| Recall | 0.950 | 0.917 | 0.033 |
| Perfect Matches | 9/10 | 8/10 | - |
| Runtime | 236.2s | 263.9s | 27.7s |

**Summary**: ChainOfThought outperforms Predict by 0.037 F1 points

### mistral:7b

| Metric | ChainOfThought | Predict | Difference |
|--------|----------------|---------|------------|
| F1 Score | 0.947 🏆 | 0.917  | 0.030 |
| Precision | 1.000 | 0.950 | 0.050 |
| Recall | 0.917 | 0.900 | 0.017 |
| Perfect Matches | 8/10 | 8/10 | - |
| Runtime | 0.0s | 79.1s | 79.0s |

**Summary**: ChainOfThought outperforms Predict by 0.030 F1 points

### gemma3:27b

| Metric | ChainOfThought | Predict | Difference |
|--------|----------------|---------|------------|
| F1 Score | 0.933 🏆 | 0.893  | 0.040 |
| Precision | 1.000 | 1.000 | 0.000 |
| Recall | 0.900 | 0.833 | 0.067 |
| Perfect Matches | 8/10 | 6/10 | - |
| Runtime | 0.1s | 0.0s | 0.1s |

**Summary**: ChainOfThought outperforms Predict by 0.040 F1 points

### llama3.2:latest

| Metric | ChainOfThought | Predict | Difference |
|--------|----------------|---------|------------|
| F1 Score | 0.863 🏆 | 0.792  | 0.071 |
| Precision | 0.900 | 0.883 | 0.017 |
| Recall | 0.867 | 0.833 | 0.033 |
| Perfect Matches | 6/10 | 5/10 | - |
| Runtime | 29.4s | 99.5s | 70.0s |

**Summary**: ChainOfThought outperforms Predict by 0.071 F1 points

### deepseek-r1:8b

| Metric | ChainOfThought | Predict | Difference |
|--------|----------------|---------|------------|
| F1 Score | 0.763  | 0.850 🏆 | 0.087 |
| Precision | 0.850 | 1.000 | 0.150 |
| Recall | 0.717 | 0.783 | 0.067 |
| Perfect Matches | 5/10 | 6/10 | - |
| Runtime | 223.6s | 264.4s | 40.9s |

**Summary**: Predict outperforms ChainOfThought by 0.087 F1 points

## Key Insights

### Overall Mode Performance

- **Average F1 Score**:
  - ChainOfThought: 0.912
  - Predict: 0.885
- **Average Runtime**:
  - ChainOfThought: 81.6s
  - Predict: 127.3s

### Mode Advantages by Model

- **ChainOfThought performs better on**: llama3.1:8b, deepseek-r1:14b, mistral:7b, gemma3:27b, llama3.2:latest
- **Predict performs better on**: deepseek-r1:8b

## Test Details

- **Total test cases per configuration**: 10
- **Test categories**: Multi-tool selection across events, e-commerce, and finance domains
- **Evaluation metrics**:
  - **F1 Score**: Harmonic mean of precision and recall
  - **Precision**: Fraction of selected tools that were correct
  - **Recall**: Fraction of expected tools that were selected
  - **Perfect Matches**: Test cases where exactly the right tools were selected
