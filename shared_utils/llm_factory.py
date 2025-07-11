"""LLM Factory for multi-provider support using DSPy's unified interface."""

import os
import dspy
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path
import logging

def setup_llm(provider: Optional[str] = None) -> dspy.LM:
    """
    Factory function to configure DSPy LLM based on provider.
    
    Args:
        provider: The LLM provider to use. If None, reads from DSPY_PROVIDER env var.
                 Options: 'ollama', 'claude', 'openai', 'gemini', etc.
    
    Returns:
        Configured dspy.LM instance
    """
    # Load environment variables
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    # Get provider from argument or environment
    provider = provider or os.getenv("DSPY_PROVIDER", "ollama")
    
    # Common settings
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1024"))
    debug = os.getenv("DSPY_DEBUG", "false").lower() == "true"
    
    print(f"🤖 Setting up {provider} LLM")
    
    # Set up logging if debug is enabled
    if debug:
        logging.getLogger("dspy").setLevel(logging.DEBUG)
        logging.basicConfig(
            level=logging.DEBUG,
            format='🔍 %(name)s - %(levelname)s - %(message)s'
        )
        print(f"   🔍 Debug logging: ENABLED")
        print(f"   💡 Use dspy.inspect_history() to see prompts/responses")
    
    # Configure based on provider
    if provider == "ollama":
        model = os.getenv("OLLAMA_MODEL", "gemma3:27b")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        print(f"   Model: {model}")
        print(f"   Base URL: {base_url}")
        llm = dspy.LM(
            model=f"ollama/{model}",
            api_base=base_url,
            temperature=temperature,
            max_tokens=max_tokens
        )
    elif provider == "claude":
        model = os.getenv("CLAUDE_MODEL", "claude-3-opus-20240229")
        print(f"   Model: {model}")
        llm = dspy.LM(
            model=f"anthropic/{model}",
            temperature=temperature,
            max_tokens=max_tokens
        )
    elif provider == "openai":
        model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        print(f"   Model: {model}")
        llm = dspy.LM(
            model=f"openai/{model}",
            temperature=temperature,
            max_tokens=max_tokens
        )
    elif provider == "gemini":
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-pro-latest")
        print(f"   Model: {model}")
        llm = dspy.LM(
            model=f"gemini/{model}",
            temperature=temperature,
            max_tokens=max_tokens
        )
    else:
        # Generic provider support using full model string
        model = os.getenv("LLM_MODEL", f"{provider}/default-model")
        print(f"   Model: {model}")
        llm = dspy.LM(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    # Test connection
    try:
        llm("Hello", max_tokens=5)
        print(f"   ✅ {provider} connection successful")
    except Exception as e:
        print(f"   ❌ {provider} connection failed: {e}")
        if provider == "claude":
            print("   💡 Make sure ANTHROPIC_API_KEY is set in your environment or cloud.env")
        elif provider == "openai":
            print("   💡 Make sure OPENAI_API_KEY is set in your environment or cloud.env")
        elif provider == "gemini":
            print("   💡 Make sure GOOGLE_API_KEY is set in your environment or cloud.env")
        raise
    
    # Configure DSPy
    dspy.settings.configure(lm=llm)
    
    return llm