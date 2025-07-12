"""
Shared models and utilities for DSPy tool selection and agentic loop.

This module contains the shared Pydantic models used by both the tool selection
system and the agentic loop implementation.
"""

from .models import (
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