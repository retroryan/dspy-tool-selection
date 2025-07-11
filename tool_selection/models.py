"""Shared data models for tool selection and registry.

This module contains all the shared Pydantic models and enums used by both
the tool selector and tool registry modules, avoiding circular imports.
"""

from enum import Enum
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class ToolArgument(BaseModel):
    """Tool argument definition.
    
    DSPy will use the Field descriptions to help the LLM understand
    what each field represents when generating structured output.
    """
    name: str = Field(description="Argument name")
    type: str = Field(description="Argument type (str, int, etc.)")
    description: str = Field(description="What this argument is for")


class MultiToolName(str, Enum):
    """Extended set of tool names for multi-tool scenarios."""
    # Events
    FIND_EVENTS = "find_events"
    CREATE_EVENT = "create_event"
    UPDATE_EVENT = "update_event"
    CANCEL_EVENT = "cancel_event"
    
    # E-commerce
    SEARCH_PRODUCTS = "search_products"
    ADD_TO_CART = "add_to_cart"
    CHECKOUT = "checkout"
    TRACK_ORDER = "track_order"
    RETURN_ITEM = "return_item"
    
    # Finance
    CHECK_BALANCE = "check_balance"
    TRANSFER_MONEY = "transfer_money"
    PAY_BILL = "pay_bill"
    INVEST = "invest"
    GET_STATEMENT = "get_statement"


class MultiTool(BaseModel):
    """Extended tool definition."""
    name: MultiToolName
    description: str
    arguments: List[ToolArgument]
    category: str


class ToolCall(BaseModel):
    """Single tool call with arguments."""
    tool_name: str  # Will be constrained by Literal in signature
    arguments: Dict[str, Any] = Field(default_factory=dict)


class MultiToolDecision(BaseModel):
    """Decision containing multiple tool calls."""
    tool_calls: List[ToolCall]
    reasoning: str