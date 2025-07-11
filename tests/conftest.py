"""Pytest configuration and shared fixtures."""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def setup_environment():
    """Set up environment variables for testing."""
    # Use a smaller model for faster tests
    os.environ["OLLAMA_MODEL"] = os.environ.get("OLLAMA_MODEL", "gemma2:2b")
    os.environ["DSPY_DEBUG"] = "false"  # Disable debug output during tests
    
    yield
    
    # Cleanup if needed
    pass


@pytest.fixture
def quiet_mode(monkeypatch):
    """Fixture to suppress stdout during tests."""
    import io
    import contextlib
    
    @contextlib.contextmanager
    def suppress_output():
        with contextlib.redirect_stdout(io.StringIO()):
            with contextlib.redirect_stderr(io.StringIO()):
                yield
    
    return suppress_output