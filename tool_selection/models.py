"""
Shared data models for tool selection and registry.

This module re-exports the shared models from the shared package for backward compatibility.
The actual models are now defined in shared/models.py to avoid duplication.
"""

# Re-export models from shared package for backward compatibility
from shared.models import ToolCall, MultiToolDecision

__all__ = ['ToolCall', 'MultiToolDecision']