#!/bin/bash

# DSPy Model Comparison Runner

# Default values
CREATE_MD=false
CSV_FILE=""
OUTPUT_FILE=""

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --models \"model1,model2\"  Comma-separated list of models to test"
    echo "  --create-md               Run csv_to_md.py to convert CSV to markdown"
    echo "  --csv input.csv          CSV file to convert (required with --create-md)"
    echo "  -o output.md             Output markdown file (required with --create-md)"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  # Run model comparison with specific models"
    echo "  ./run_model_comparison.sh --models \"gemma3:27b,llama3.1:8b\""
    echo ""
    echo "  # Convert CSV to markdown"
    echo "  ./run_model_comparison.sh --create-md --csv input.csv -o output.md"
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --models)
            MODELS="$2"
            shift 2
            ;;
        --create-md)
            CREATE_MD=true
            shift
            ;;
        --csv)
            CSV_FILE="$2"
            shift 2
            ;;
        -o)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# If --create-md is specified, run csv_to_md.py
if [ "$CREATE_MD" = true ]; then
    if [ -z "$CSV_FILE" ] || [ -z "$OUTPUT_FILE" ]; then
        echo "Error: --create-md requires both --csv and -o options"
        echo "Example: ./run_model_comparison.sh --create-md --csv input.csv -o output.md"
        exit 1
    fi
    
    echo "📊 Converting CSV to Markdown"
    echo "  Input: $CSV_FILE"
    echo "  Output: $OUTPUT_FILE"
    echo ""
    
    poetry run python -m tool_selection.csv_to_md "$CSV_FILE" "$OUTPUT_FILE"
    exit $?
fi

# Otherwise, run model comparison
echo "🦙 DSPy Model Comparison"
echo "======================="
echo ""

# Run setup if needed
if [ ! -d ".venv" ] || [ ! -f ".env" ]; then
    echo "Running setup first..."
    ./setup.sh
    if [ $? -ne 0 ]; then
        echo "Setup failed. Please fix the issues and try again."
        exit 1
    fi
    echo ""
fi

# Build command
CMD="poetry run python -m tool_selection.run_model_comparison"

if [ ! -z "$MODELS" ]; then
    CMD="$CMD --models \"$MODELS\""
fi

# Run the comparison
echo "🚀 Running model comparison..."
echo ""
eval $CMD