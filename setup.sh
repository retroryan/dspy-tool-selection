#!/bin/bash

# DSPy Tool Selection Demo Setup Script
# This script handles all setup and dependency installation

echo "🔧 DSPy Tool Selection Demo Setup"
echo "================================="
echo ""

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install Poetry first."
    echo "   Visit: https://python-poetry.org/docs/#installation"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    
    # Get list of available Ollama models
    AVAILABLE_MODELS=""
    if command -v ollama &> /dev/null && ollama list &> /dev/null; then
        AVAILABLE_MODELS=$(ollama list | tail -n +2 | awk '{print $1}' | sed 's/^/# Available: /')
    fi
    
    # Create .env file with available models as comments
    cat > .env << EOF
# DSPy Simple Tool Selection Demo Configuration

# Ollama Configuration
OLLAMA_MODEL=gemma3:27b
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MAX_TOKENS=1024
OLLAMA_TEMPERATURE=0.7

# Your available Ollama models:
${AVAILABLE_MODELS:-# (Could not retrieve model list - is Ollama running?)}

# Demo Configuration
DEMO_VERBOSE=true

# DSPy Mode Configuration
# Set to "true" to use Predict mode (direct prediction)
# Set to "false" to use Chain of Thought mode (step-by-step reasoning)
DSPY_USE_PREDICT=false
EOF
    echo "✅ Created .env file with defaults"
    echo ""
fi

# Install dependencies if needed
if [ ! -d ".venv" ]; then
    echo "📦 Installing dependencies..."
    poetry install
    echo ""
else
    echo "✅ Dependencies already installed"
fi

# Check if Ollama is running
if command -v ollama &> /dev/null; then
    if ollama list &> /dev/null; then
        echo "✅ Ollama is running"
        
        # Check if gemma3:27b model is available (note: project defaults to gemma3:27b)
        if ollama list | grep -q "gemma3:27b"; then
            echo "✅ Model gemma3:27b is available (recommended for best tool calling)"
        else
            echo ""
            echo "⚠️  Model gemma3:27b not found!"
            echo ""
            echo "   This project was primarily tested with gemma3:27b, which is"
            echo "   recommended for best tool calling performance."
            echo ""
            echo "   To install the recommended model:"
            echo "   ollama pull gemma3:27b"
            echo ""
            echo "   Your available models:"
            ollama list | tail -n +2 | awk '{print "   - " $1}'
            echo ""
            echo "   You can use a different model by updating OLLAMA_MODEL in .env"
        fi
    else
        echo "⚠️  Ollama is not running. Start it with: ollama serve"
    fi
else
    echo "⚠️  Ollama is not installed. Visit: https://ollama.ai/"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the demo:"
echo "  ./run_demo.sh          # Run in Chain of Thought mode (default)"
echo "  ./run_demo.sh predict  # Run in Predict mode"
echo ""