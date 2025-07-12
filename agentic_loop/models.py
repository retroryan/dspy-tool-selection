"""
Core data models for the agentic loop implementation.

This module re-exports the shared models from the shared package for backward compatibility.
The actual models are now defined in shared/models.py to avoid duplication.
"""

# Re-export models from shared package for backward compatibility
from shared.models import (
    # Core tool models
    ToolCall,
    MultiToolDecision,
    
    # Agentic loop models
    ActionType,
    ReasoningOutput,
    ActionDecision,
    ConversationState,
    ErrorRecoveryStrategy,
    ToolExecutionResult,
    ActivityResult
)

__all__ = [
    # Core tool models
    'ToolCall',
    'MultiToolDecision',
    
    # Agentic loop models
    'ActionType',
    'ReasoningOutput',
    'ActionDecision',
    'ConversationState',
    'ErrorRecoveryStrategy',
    'ToolExecutionResult',
    'ActivityResult'
]