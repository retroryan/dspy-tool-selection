#!/bin/bash

# DSPy Agentic Loop Cloud Model Comparison Runner

# Function to show usage
show_usage() {
    echo "Usage: $0 [TOOL_SET] [OPTIONS]"
    echo ""
    echo "Arguments:"
    echo "  TOOL_SET                 Tool set to test models against (default: productivity)"
    echo "                          Available: treasure_hunt, productivity, ecommerce"
    echo ""
    echo "Options:"
    echo "  --providers \"p1,p2\"     Comma-separated list of providers to test"
    echo "                          Available: claude, openai"
    echo "  --models \"model1,model2\" Comma-separated list of specific models to test"
    echo "                          You can specify any model IDs supported by the providers"
    echo "  --advanced              Use advanced agentic loop with enhanced reasoning"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  # Test default models from all available providers"
    echo "  ./run_cloud_model_comparison.sh"
    echo ""
    echo "  # Test specific tool set with Claude models only"
    echo "  ./run_cloud_model_comparison.sh treasure_hunt --providers \"claude\""
    echo ""
    echo "  # Test specific models with advanced mode"
    echo "  ./run_cloud_model_comparison.sh ecommerce --models \"claude-3-haiku-20240307\" --advanced"
    echo ""
    echo "  # Test with advanced agentic loop"
    echo "  ./run_cloud_model_comparison.sh ecommerce --advanced"
    exit 0
}

# Default values
TOOL_SET=""
PROVIDERS=""
MODELS=""
ADVANCED_MODE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --providers)
            PROVIDERS="$2"
            shift 2
            ;;
        --models)
            MODELS="$2"
            shift 2
            ;;
        --advanced)
            ADVANCED_MODE=true
            shift
            ;;
        -h|--help)
            show_usage
            ;;
        --*)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
        *)
            # This is the tool set argument
            if [ -z "$TOOL_SET" ]; then
                TOOL_SET="$1"
            else
                echo "Error: Multiple tool sets specified"
                echo "Use --help for usage information"
                exit 1
            fi
            shift
            ;;
    esac
done

echo "☁️  DSPy Agentic Loop Cloud Model Comparison"
echo "=========================================="
echo ""

# Set advanced mode if enabled
if [ "$ADVANCED_MODE" = true ]; then
    export AGENT_USE_ADVANCED=true
    echo "🚀 Advanced mode enabled"
    echo "  • Tool result analysis"
    echo "  • Goal tracking and progress monitoring"
    echo "  • Dynamic strategy adaptation"
    echo "  • Enhanced error recovery"
    echo ""
fi

# Check if cloud_test.env exists
if [ ! -f "cloud_test.env" ]; then
    echo "❌ cloud_test.env not found"
    echo "   Please create cloud_test.env with your API keys:"
    echo "   - ANTHROPIC_API_KEY for Claude models"
    echo "   - OPENAI_API_KEY for OpenAI models"
    exit 1
fi

# Run setup if needed
if [ ! -d ".venv" ]; then
    echo "Running setup first..."
    ./setup.sh
    if [ $? -ne 0 ]; then
        echo "Setup failed. Please fix the issues and try again."
        exit 1
    fi
    echo ""
fi

# Build command
CMD="poetry run python -m agentic_loop.run_cloud_model_comparison"

# Add tool set if specified
if [ -n "$TOOL_SET" ]; then
    CMD="$CMD $TOOL_SET"
else
    echo "📦 Using default tool set: productivity"
fi

# Add providers if specified
if [ -n "$PROVIDERS" ]; then
    CMD="$CMD --providers \"$PROVIDERS\""
else
    echo "☁️  Using all available providers with API keys"
fi

# Add models if specified
if [ -n "$MODELS" ]; then
    CMD="$CMD --models \"$MODELS\""
else
    echo "🤖 Using default models: First 2 from each provider"
fi

if [ "$ADVANCED_MODE" = true ]; then
    echo "🔧 Mode: Advanced Agentic Loop"
else
    echo "🔧 Mode: Basic Agentic Loop"
fi

# Run the comparison
echo ""
echo "🚀 Running cloud model comparison..."
echo ""
eval $CMD

# Show where results are saved
if [ $? -eq 0 ]; then
    echo ""
    echo "📁 Results Location:"
    echo "   Check the test_results/ directory for detailed JSON output"
    echo "   Latest results: test_results/cloud_model_comparison_${TOOL_SET:-productivity}_*.json"
    echo ""
    echo "   View results with:"
    echo "   cat test_results/cloud_model_comparison_*.json | tail -1 | jq ."
fi